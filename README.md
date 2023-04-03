# Blog project in FastAPI and MongoDB-ODM

This is a **Blog** API project using <a href="https://mongodb-odm.readthedocs.io" class="external-link" target="_blank">MongoDB-ODM</a> in <a href="https://fastapi.tiangolo.com" class="external-link" target="_blank">FastAPI</a>

## Start project

### First

Clone the repository and navigate to the project.

```bash
git clone https://github.com/nayan32biswas/blog-with-FastApi-and-MongoDB-ODM.git
cd blog-with-FastApi-and-MongoDB-ODM
```

## Run with Docker

Make sure you have docker installed and active.

```bash
docker-compose up --build api
```

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
