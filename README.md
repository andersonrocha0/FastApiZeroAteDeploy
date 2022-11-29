# Pré reqs MAC OS

brew install postgresql

# Rodar banco com Docker

docker run --name db_fast_api_zero_ate_deploy -p 5432:5432 -e POSTGRES_DB=d
b_fast_api_zero_ate_deploy -e POSTGRES_PASSWORD=1234 -d postgre


# Aplicar migrations no banco de dados



