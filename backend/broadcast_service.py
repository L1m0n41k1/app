import asyncio
import logging
import time
import random
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BroadcastService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.active_broadcasts = {}
        self.drivers = {}  # Хранение драйверов для каждого аккаунта
        self.locks = {}    # Блокировки для каждого аккаунта

    def get_chrome_options(self) -> Options:
        """Настройки Chrome для имитации desktop браузера"""
        options = Options()
        
        # Desktop User Agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Базовые настройки
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Размер окна (desktop)
        options.add_argument('--window-size=1920,1080')
        
        # Отключение изображений для ускорения (опционально)
        # options.add_argument('--disable-images')
        
        # Скрытый режим для production
        # options.add_argument('--headless')
        
        return options

    async def get_account_driver(self, account_id: str, platform: str) -> webdriver.Chrome:
        """Получить или создать драйвер для аккаунта"""
        if account_id not in self.drivers:
            options = self.get_chrome_options()
            
            # Уникальный профиль для каждого аккаунта
            profile_path = f"/tmp/chrome_profile_{account_id}"
            options.add_argument(f'--user-data-dir={profile_path}')
            
            driver = webdriver.Chrome(options=options)
            
            # Убираем признаки автоматизации
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.drivers[account_id] = driver
            self.locks[account_id] = threading.Lock()
            
            # Предварительная авторизация (если нужно)
            await self._ensure_account_authorized(account_id, platform, driver)
        
        return self.drivers[account_id]

    async def _ensure_account_authorized(self, account_id: str, platform: str, driver: webdriver.Chrome):
        """Проверка авторизации аккаунта"""
        try:
            if platform == 'whatsapp':
                driver.get('https://web.whatsapp.com')
                # Проверяем наличие QR кода
                try:
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.XPATH, "//div[@data-testid='qrcode']"))
                    )
                    logger.info(f"WhatsApp account {account_id} is authorized")
                except TimeoutException:
                    logger.warning(f"WhatsApp account {account_id} requires authorization")
                    
            elif platform == 'telegram':
                driver.get('https://web.telegram.org/k/')
                # Проверяем, что мы не на странице авторизации
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".chat-list, .input-search"))
                    )
                    logger.info(f"Telegram account {account_id} is authorized")
                except TimeoutException:
                    logger.warning(f"Telegram account {account_id} requires authorization")
                    
        except Exception as e:
            logger.error(f"Error checking authorization for {account_id}: {str(e)}")

    async def start_broadcast(self, job_id: str, user_id: str, account_id: str, 
                            platform: str, recipients: List[Dict], templates: List[str], 
                            template_mode: str = 'random') -> bool:
        """Запуск рассылки"""
        try:
            # Обновляем статус задания
            await self.db.broadcast_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": "running",
                        "started_at": datetime.utcnow(),
                        "logs": [f"Начало рассылки в {datetime.now().strftime('%H:%M:%S')}"]
                    }
                }
            )

            # Получаем драйвер для аккаунта
            driver = await self.get_account_driver(account_id, platform)
            
            # Запускаем рассылку в отдельном потоке
            self.active_broadcasts[job_id] = True
            
            if platform == 'whatsapp':
                success = await self._send_whatsapp_broadcast(
                    job_id, driver, recipients, templates, template_mode
                )
            elif platform == 'telegram':
                success = await self._send_telegram_broadcast(
                    job_id, driver, recipients, templates, template_mode
                )
            else:
                raise ValueError(f"Unsupported platform: {platform}")

            # Обновляем финальный статус
            final_status = "completed" if success else "failed"
            await self.db.broadcast_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": final_status,
                        "completed_at": datetime.utcnow()
                    },
                    "$push": {
                        "logs": f"Рассылка завершена со статусом: {final_status}"
                    }
                }
            )

            return success

        except Exception as e:
            logger.error(f"Broadcast error for job {job_id}: {str(e)}")
            await self.db.broadcast_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {"status": "failed", "completed_at": datetime.utcnow()},
                    "$push": {"logs": f"Ошибка: {str(e)}"}
                }
            )
            return False
        finally:
            if job_id in self.active_broadcasts:
                del self.active_broadcasts[job_id]

    async def _send_whatsapp_broadcast(self, job_id: str, driver: webdriver.Chrome, 
                                     recipients: List[Dict], templates: List[str], 
                                     template_mode: str) -> bool:
        """Рассылка через WhatsApp"""
        successful_sends = 0
        failed_sends = 0
        
        with self.locks.get(driver.session_id, threading.Lock()):
            for i, recipient in enumerate(recipients):
                if job_id not in self.active_broadcasts:
                    break  # Остановка рассылки
                
                try:
                    phone = recipient['contact_info']
                    # Выбираем шаблон
                    if template_mode == 'random':
                        message = random.choice(templates)
                    else:  # alternating
                        message = templates[i % len(templates)]
                    
                    success = await self._send_whatsapp_message(driver, phone, message, job_id)
                    
                    if success:
                        successful_sends += 1
                        await self._log_broadcast(job_id, f"✅ Отправлено: {phone}")
                    else:
                        failed_sends += 1
                        await self._log_broadcast(job_id, f"❌ Ошибка: {phone}")
                    
                    # Обновляем прогресс
                    await self.db.broadcast_jobs.update_one(
                        {"id": job_id},
                        {
                            "$set": {
                                "successful_sends": successful_sends,
                                "failed_sends": failed_sends
                            }
                        }
                    )
                    
                    # Пауза между сообщениями
                    await asyncio.sleep(random.uniform(3, 7))
                    
                except Exception as e:
                    failed_sends += 1
                    await self._log_broadcast(job_id, f"❌ Критическая ошибка для {recipient.get('contact_info', 'unknown')}: {str(e)}")
        
        return successful_sends > 0

    async def _send_whatsapp_message(self, driver: webdriver.Chrome, phone: str, 
                                   message: str, job_id: str) -> bool:
        """Отправка одного сообщения в WhatsApp"""
        try:
            # Проверяем QR код ПЕРЕД отправкой
            driver.get(f"https://web.whatsapp.com/send?phone={phone}")
            
            # Проверка QR кода
            try:
                qr_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='qrcode']"))
                )
                if qr_element:
                    await self._log_broadcast(job_id, "❌ Обнаружен QR код - аккаунт не авторизован")
                    raise Exception("Account not authorized - QR code detected")
            except TimeoutException:
                pass  # QR код не найден - хорошо
            
            # Ждем загрузки чата
            try:
                input_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
                )
            except TimeoutException:
                # Повторная проверка QR кода
                qr_elements = driver.find_elements(By.XPATH, "//div[@data-testid='qrcode']")
                if qr_elements:
                    raise Exception("Account blocked - QR code appeared during broadcast")
                raise Exception("Chat input field not found")
            
            input_field.clear()
            
            # Имитация человеческого ввода
            for line in message.split('\n'):
                if job_id not in self.active_broadcasts:
                    return False
                input_field.send_keys(line)
                input_field.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Удаляем последний перенос строки
            input_field.send_keys(Keys.BACKSPACE)
            
            # Отправка
            send_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Отправить']"))
            )
            send_button.click()
            
            # Проверка доставки (галочки)
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-icon='msg-dblcheck'], span[aria-label='Read'], span[data-testid='msg-time']"))
                )
                return True
            except TimeoutException:
                await self._log_broadcast(job_id, f"⚠️ Не удалось подтвердить доставку для {phone}")
                return True  # Считаем успешным, если отправили
                
        except Exception as e:
            logger.error(f"WhatsApp send error for {phone}: {str(e)}")
            return False

    async def _send_telegram_broadcast(self, job_id: str, driver: webdriver.Chrome, 
                                     recipients: List[Dict], templates: List[str], 
                                     template_mode: str) -> bool:
        """Рассылка через Telegram"""
        successful_sends = 0
        failed_sends = 0
        
        with self.locks.get(driver.session_id, threading.Lock()):
            for i, recipient in enumerate(recipients):
                if job_id not in self.active_broadcasts:
                    break
                
                try:
                    username = recipient['contact_info']
                    # Выбираем шаблон
                    if template_mode == 'random':
                        message = random.choice(templates)
                    else:
                        message = templates[i % len(templates)]
                    
                    success = await self._send_telegram_message(driver, username, message, job_id)
                    
                    if success:
                        successful_sends += 1
                        await self._log_broadcast(job_id, f"✅ Отправлено: {username}")
                    else:
                        failed_sends += 1
                        await self._log_broadcast(job_id, f"❌ Ошибка: {username}")
                    
                    # Обновляем прогресс
                    await self.db.broadcast_jobs.update_one(
                        {"id": job_id},
                        {
                            "$set": {
                                "successful_sends": successful_sends,
                                "failed_sends": failed_sends
                            }
                        }
                    )
                    
                    # Пауза между сообщениями
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    failed_sends += 1
                    await self._log_broadcast(job_id, f"❌ Критическая ошибка для {recipient.get('contact_info', 'unknown')}: {str(e)}")
        
        return successful_sends > 0

    async def _send_telegram_message(self, driver: webdriver.Chrome, username: str, 
                                   message: str, job_id: str) -> bool:
        """Отправка одного сообщения в Telegram"""
        try:
            # Открываем новую вкладку
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            
            # Переходим к чату
            clean_username = username.replace('@', '').strip()
            url = f"https://web.telegram.org/k/#{username}"
            driver.get(url)
            
            # Проверяем авторизацию
            try:
                input_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.input-message-input"))
                )
                
                # Дополнительная проверка загрузки чата
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.chat-info"))
                )
                
            except TimeoutException:
                # Проверяем, не на странице ли авторизации
                if "login" in driver.current_url:
                    raise Exception("Account blocked - redirected to login page")
                else:
                    raise Exception(f"Chat with {username} not found or not loaded")
            
            time.sleep(1)  # Дополнительное время для загрузки
            
            # Находим поле ввода
            input_field = driver.find_element(By.CSS_SELECTOR, "div.input-message-input")
            input_field.click()
            time.sleep(0.2)
            input_field.clear()
            time.sleep(0.3)
            
            # Имитация ввода
            for line in message.split('\n'):
                if job_id not in self.active_broadcasts:
                    return False
                input_field.send_keys(line)
                input_field.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(random.uniform(0.05, 0.1))
            
            # Удаляем последний перенос
            input_field.send_keys(Keys.BACKSPACE)
            
            # Отправка
            send_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-icon.send")
            send_btn.click()
            
            # Проверка доставки
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.bubble:last-child .message-date"))
                )
            except TimeoutException:
                await self._log_broadcast(job_id, f"⚠️ Не удалось подтвердить доставку для {username}")
            
            return True
            
        except Exception as e:
            logger.error(f"Telegram send error for {username}: {str(e)}")
            return False
        finally:
            # Закрываем вкладку
            try:
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
            except:
                pass

    async def _log_broadcast(self, job_id: str, message: str):
        """Добавить лог к заданию"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        await self.db.broadcast_jobs.update_one(
            {"id": job_id},
            {"$push": {"logs": log_message}}
        )
        
        logger.info(f"Job {job_id}: {log_message}")

    async def stop_broadcast(self, job_id: str) -> bool:
        """Остановка рассылки"""
        if job_id in self.active_broadcasts:
            del self.active_broadcasts[job_id]
            
            await self.db.broadcast_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {"status": "paused", "completed_at": datetime.utcnow()},
                    "$push": {"logs": "Рассылка остановлена пользователем"}
                }
            )
            return True
        return False

    def cleanup_driver(self, account_id: str):
        """Очистка драйвера аккаунта"""
        if account_id in self.drivers:
            try:
                self.drivers[account_id].quit()
            except:
                pass
            del self.drivers[account_id]
            if account_id in self.locks:
                del self.locks[account_id]

    def cleanup_all_drivers(self):
        """Очистка всех драйверов"""
        for account_id in list(self.drivers.keys()):
            self.cleanup_driver(account_id)