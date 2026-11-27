# Асинхронные задачи на RabbitMQ

* HTTP API принимает задачу, кладёт её в очередь и сразу отвечает
  202 Accepted. Потом отдельно читает очередь результатов.
* Обработчик берёт задачу из очереди, ждёт 2,5 секунды и
  отправляет результат обратно в очередь.
* RabbitMQ - брокер сообщений с management UI.

## Запуск

Нужен Docker Desktop с Docker Compose. В папке проекта выполнить:

```bash
docker compose up --build
```

Первый запуск занимает пару минут, т.к. скачиваются образы и ставятся зависимости.
Когда в логах появится "Жду задачи в очереди tasks", можно работать.

Если нужен запуск в фоне:

```bash
docker compose up --build -d
docker compose ps
```

Адреса:

* API: <http://localhost:8000>
* Swagger: <http://localhost:8000/docs>
* RabbitMQ UI: <http://localhost:15672>
* Логин и пароль RabbitMQ: `app` / `app_secret`

## Проверка через curl

### 1. Отправить задачу

PowerShell:

```powershell
'{"topic":"prepare report"}' | curl.exe -sS -i -X POST http://localhost:8000/jobs -H "Content-Type: application/json" --data-binary '@-'
```

bash:

```bash
curl -sS -i -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"topic":"prepare report"}'
```

Ответ должен прийти сразу, без ожидания 2,5 секунды:

```http
HTTP/1.1 202 Accepted
content-type: application/json

{"id":"0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01","status":"ACCEPTED"}
```

id будет другим. Скопируйте его для следующего запроса.

### 2. Посмотреть статус сразу

PowerShell:

```powershell
curl.exe -sS http://localhost:8000/jobs/0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01
```

bash:

```bash
curl -sS http://localhost:8000/jobs/0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01
```

Пока Обработчик ещё работает:

```json
{
  "id": "0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01",
  "topic": "prepare report",
  "status": "ACCEPTED",
  "result": null,
  "completedAt": null
}
```

### 3. Посмотреть статус через 3 секунды

PowerShell:

```powershell
Start-Sleep -Seconds 3
curl.exe -sS http://localhost:8000/jobs/0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01
```

bash:

```bash
sleep 3
curl -sS http://localhost:8000/jobs/0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01
```

Ожидаемо:

```json
{
  "id": "0b6f5f4e-3d8c-4f6a-9d5e-2a7c1b8e9f01",
  "topic": "prepare report",
  "status": "DONE",
  "result": "Задача 'prepare report' выполнена",
  "completedAt": "2026-11-27T13:31:45Z"
}
```

## RabbitMQ UI в очереди

1. Откройте <http://localhost:15672>.
2. Войдите как `app` / `app_secret`.
3. Откройте вкладку **Queues and Streams**.

Там будут две очереди:

* tasks - сюда сервис A кладёт задачи;
* results - сюда сервис B кладёт результаты.

Во время обработки задачи в tasks будет Unacked = 1. После завершения обе очереди будут пустыми.

Можно остановить обработчик и увидеть, как задачи копятся:

```bash
docker compose stop service-b
```

После нескольких POST /jobs в очереди tasks появится Ready > 0.
Вернуть обработчик:

```bash
docker compose start service-b
```

## Как это работает

1. Клиент отправляет POST /jobs с темой задачи.
2. HTTP API создаёт id, сохраняет задачу в памяти и публикует в очередь
   `tasks` JSON:

   ```json
   {"id": "...", "topic": "prepare report"}
   ```

3. HTTP API сразу отвечает `202 Accepted`. Работу выполняет не он.
4. Обработчик читает задачу, ждёт 2.5 секунды и публикует в очередь results
   событие:

   ```json
   {
     "type": "JobCompleted",
     "id": "...",
     "result": "Задача 'prepare report' выполнена",
     "completedAt": "2026-11-27T13:31:45Z"
   }
   ```

5. Фоновый поток HTTP API читает results и меняет статус задачи на DONE.
6. GET /jobs/{id} возвращает статус и результат.




## Обработчик защищён от дублей

1. Обработчик хранит множество processed с id уже обработанных задач. Если
   RabbitMQ повторно отдал ту же задачу, B не спит 2.5 секунды второй раз, а
   сразу подтверждает её.
2. HTTP API меняет статус на DONE только один раз. Если результат пришёл
   повторно, A его игнорирует.

## Остановка

```bash
docker compose down
```

Для запуска заново:

```bash
docker compose up --build
```

## Если что-то не работает

* docker compose logs service-a service-b rabbitmq - посмотреть ошибки.
* docker compose ps - проверить, что все три контейнера запущены.
* Если порт 8000, 5672 или 15672 занят, остановите программу, которая его
  использует, или измените порты в docker-compose.yml.
* После изменения кода пересоберите образы. docker compose up --build.
