# Pré reqs MAC OS

brew install postgresql

```
Se quiser rodar o postgres como serviço no mac, use o código abaixo
  brew services start postgresql@14
Se quiser rodar pelo terminal e ter a possibilidade de para quando quiser, utilize o seguinte comando
  /opt/homebrew/opt/postgresql@14/bin/postgres -D /opt/homebrew/var/postgresql@14
```

# Rodar banco com Docker

docker run --name db_fast_api_zero_ate_deploy -p 5432:5432 -e POSTGRES_DB=db_fast_api_zero_ate_deploy -e POSTGRES_PASSWORD=1234 -d postgres


# Versão atual do python

3.12

# Aplicar migrations no banco de dados

```
alembic upgrade head
```
