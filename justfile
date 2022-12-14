set dotenv-load

export EDITOR := 'nvim'

alias f := fmt
alias r := run

default:
  just --list

fmt:
  isort . && yapf --in-place --recursive main.py && prettier --write .

run *args:
  python3.9 main.py {{args}}
