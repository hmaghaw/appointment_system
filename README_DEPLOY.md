# Deployment
## For the first time or when dependancies change
docker-compose build 

## Everytime
docker-compose up -d

# Stop only api while keeping db running
```angular2html
docker-compose stop api
docker-compose rm -f api

```

## Restarting it again
```angular2html
docker-compose up -d api

```