# CDI Project - текстовый помошник для построения стратегия развития ЦДИ до 2030 года

#### Описание
Этот проект предназначен для помощи в разработки стратегии развития Центра Дигитализации и Инноваций (ЦДИ) до 2030 года. В рамках проекта происходит сбор, обработка и анализ нормативных документов, которые будут использованы для формирования рекомендаций и планов развития.

### Особенности проекта
- Автоматизация обработки нормативной документации
- Конвертация PDF документов в структурированный формат JSON
- Использование Elasticsearch для индексации и поиска по тексту документов
- Поддержка запросов на естественном языке для удобного доступа к информации
- WEB-API для взаимодействия с пользователем

### Текущие результаты
Проект находится в стадии разработки. На данном этапе:
- Обеспечена начальная обработка и конвертация документов
- Добавлен препроцессинг текстов в виде исправления орфаграфии и лематизации
- Настроены базовые индексационные процессы для Elasticsearch
- Начата работа над интеграцией поиска с использованием естественного языка
- Создан веб интерфейс (API) для взаимодействия с пользователем или веб-приложением
- Упрощён деплой проекта за счёт использования Docker и Docker Compose
- Добавлена проверка на наличие файла, чтобы предотвратить повторные загрузки одних и тех же документов
- Приложение полностью написанно асинхронно
- Настроена оптимизация потока запросов на поиск с помощью Redis

### Приоритетные цели
- Добавить удаление стоп-слов и пунктуации в препроцессинг

### Дополнительные цели
- Оптимизировать и улучшить качество поиска по документам

## Хранение файлов
Загруженные PDF файлы сохраняются в папке `pdfs`. Лимит размера файла — 20 МБ.

## Фоновые процессы
Разбор PDF и индексация в Elasticsearch выполняются в фоновом режиме с использованием потоков. Для общения между потоками используются записи в Redis.


# Установка приложения
Следуйте этим шагам для установки и запуска приложения.

## 1. Клонирование репозитория и переход в созданную папку:
```bash
git clone https://github.com/GaganovAlexander/CDI-project && cd CDI-project
```

## 2. Запуск скрипта настройки
Для создания `.env` файла, необходимого для корректной работы приложения, запустите скрипт `setup.sh`. Это можно сделать с помощью следующей команды:
```bash
source ./setup.sh
```

## 3. Запуск приложения с использованием Docker Compose
После того как .env файл будет создан, вы можете запустить приложение с помощью Docker Compose.

Соберите образы:
```bash
docker compose build
```
Запустите контейнеры:
```bash
docker compose up -d
```
Чтобы проверить статус контейнеров, используйте:
```bash
docker compose ps
```
Если вам нужно остановить контейнеры:
```bash
docker compose down
```

## Настройка Nginx
Добавьте в Nginx блок(пример без SSL):
```nginx
server {
  listen 80;
  server_name <ВАШ ДОМЕН ИЛИ ip-АДРЕСС>;

  client_max_body_size 20M; 

  location / {
    proxy_pass http://127.0.0.1:<ПОРТ, КОТОРЫЙ ВЫ УКАЗАЛИ КАК APP_PORT ВО ВРЕМЯ КОНФИГУРАЦИИ setup.sh>;
  }

  location /pdfs {
    root <ПОЛНЫЙ ПУТЬ ДО ПАПКИ ПРОЕКТА (ЕСЛИ НАЗВАНИЕ НЕ МЕНЯЛИ, КОНЕЧНАЯ ПАПКА - CDI-project)>;
  }
}
```
Не забудьте перезапустить Nginx:
```bash
sudo service nginx reload
```

# Документация к API для обработки PDF
Этот API предоставляет конечные точки для загрузки, обработки и поиска PDF документов. Он обрабатывает загруженные PDF, сохраняет их содержимое в Elasticsearch и позволяет пользователям искать по ним с использованием естественного языка.

## Конечные точки
### 1. Загрузка PDF
**POST /upload**

Эта конечная точка позволяет загружать PDF файл для обработки. Вы можете либо загрузить файл напрямую, либо предоставить URL на PDF файл.

#### Тело запроса (Form Data)
- **file**: PDF файл для загрузки (необязательно при наличии file_url).
- **file_url**: URL PDF файла для загрузки (необязательно при наличии file).

#### Ответ
- **200 OK**:

  Если файл успешно загружен и обработка началась.
  ```json
  {
    "message": "File uploaded successfully, processing started",
    "task_id": 1
  }
  ```
- **400 Bad Request**: 

  Если нет сразу обоих полей file и file_url
  ```json
  {
    "error": "No file or file URL provided"
  }
  ```
  Если есть поле file, но самого файла нет
  ```json
  {
    "error": "No selected file"
  }
  ```
  Если выбран файл не в формате .pdf
  ```json
  {
    "error": "Invalid file format, only PDF allowed"
  }
  ```
- **409 Conflict**
  ```json
  {
    "error": "File has already been uploaded"
  }
  ```

### 2. Получение прогресса обработки
**GET /progress/<task_id>**

Эта конечная точка позволяет проверить прогресс выполнения конкретной задачи. Возвращает текущий прогресс разбора PDF и индексации документа в Elasticsearch.

#### Параметры запроса
- **task_id**: Уникальный идентификатор задачи, для которой нужно получить прогресс.

#### Ответ
- **200 OK**: Если задача существует и обрабатывается или уже закончена.
  ```json
  {
    "pdf_parsing_progress": 50,
    "adding_doc_to_elastic_progress": 25
  }
  ```
- **404 Not Found**: Если задача не существует или не началась.
  ```json
  {
    "error": "Task not found or not started yet"
  }
  ```

### 3. Поиск по запросу
**POST /search**

Эта конечная точка позволяет искать документы, сохраненные в Elasticsearch, по запросу пользователя.

#### Запрос
- **query**: Поисковый запрос.

#### Тело запроса (JSON)
```json
{
  "query": "поисковый запрос"
}
```

#### Ответ
- **200 OK**: Если запрос успешно обработан.
  ```json
  {
    "results": [
      {
            "bbox": [
                70.94400024414062,
                570.1958618164062,
                527.9199829101562,
                678.9252319335938
            ],
            "document_name": "файл.pdf",
            "page_number": 1,
            "paragraph_number": 10,
            "score": 2.5717645,
            "text": "текс параграфа"
        },
      ...
    ]
  }
  ```
- **400 Bad Request**: Если запрос не был предоставлен.
  ```json
  {
    "error": "No query provided"
  }
  ```

### 4. Путь к pdf файлам на сервере
**GET /pdfs/<имя файла: str>**

Эта конечная точка позволит получить pdf файл с сервера, чтобы после отобразить его пользователю

#### Параметры запроса
- **<имя файла>** - такое же как в поле document_name в ответе на **/search**

#### Ответ
- **200, .pdf файл**: если такой файл есть
- **404**: если такого файла нет
