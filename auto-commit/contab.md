### add on crontab

```bash
crontab -e
```

```bash
10 0 * * * /home/diego/git/diegopacheco/python-playground/auto-commit/auto-commit.sh >> /home/diego/auto-commit.log 2>&1
```