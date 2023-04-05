# Blog project in FastAPI and MongoDB-ODM

This is a **Blog** API project using <a href="https://mongodb-odm.readthedocs.io" class="external-link" target="_blank">MongoDB-ODM</a> in <a href="https://fastapi.tiangolo.com" class="external-link" target="_blank">FastAPI</a>

## Start project

### First

Clone the repository and navigate to the project.

```bash
git clone https://github.com/nayan32biswas/blog-with-FastApi-and-MongoDB-ODM.git
cd blog-with-FastApi-and-MongoDB-ODM
```

### [Install Poetry](https://python-poetry.org/docs/#installation){.internal-link target=\_blank}

We are using poetry to manage our python package.

So we need to install poetry to start project.

### Install Dependency

Install all dependency.

```bash
poetry install
```

### Start Mongodb Server

#### [Install MongoDB](https://www.mongodb.com/docs/manual/installation/){.internal-link target=\_blank}

Install mongodb by following there official doc.

Start mongodb server.

### Export env key

```bash
export SECRET_KEY=your-secret-key
export MONGO_URL=mongodb://localhost:27017/blog_db
export DEBUG=True
```

### Run Server

Run backend server with `unicorn`.

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Run with Docker

Make sure you have docker installed and active.

Run backend server with single command.

```bash
docker-compose up --build api
```

## Visit API Documentation

Open your browser and visit [http://localhost:8000/docs](http://localhost:8000/docs)

### Create Indexes

To create indexes run this command on separate terminals:

```bash
docker-compose run --rm api python -m app.main create-indexes
```

## Visit API Docs

Open your browser with url `http://localhost:8000/docs`.

You will find all the necessary API documentation there.

## Test

### Test with Docker

```bash
docker-compose run --rm api ./scripts/test.sh
```

## Populate Data

```bash
docker-compose run --rm api python -m app.main populate-data --total-user 100 --total-post 100
```

## Clean Data

```bash
docker-compose run --rm api python -m app.main delete-data
```
