ssh -D 8080 robert@$(python $(dirname "$0")/../intermediary_info.py | sed -e 's/:/ -p /')
