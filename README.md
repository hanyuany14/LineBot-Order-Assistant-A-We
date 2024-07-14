# LineBot-Order-Assistant-A-We

這個專案是一個基於 Line Bot 的訂單助理系統，通過多個代理和模型協同工作，實現自動化訂單處理和查詢。

![Awe flowchart](https://github.com/hanyuany14/LineBot-Order-Assistant-A-We/assets/139206587/fcdd6e21-4539-4f3a-b1cf-94df4b20e0df)

# 地端自建 PGSql Server

## 啟動 PostgreSQL 伺服器

```bash
pg_ctl -D /usr/local/var/postgres restart
```

## 確認 PostgreSQL 伺服器狀態

```bash
pg_ctl -D /usr/local/var/postgres status
```

## 連接到 PostgreSQL 數據庫

```bash
psql -h 127.0.0.1 -p 5432 -U myuser -d database_1
```

## 如果無法啟動 PostgreSQL 伺服器

1. 顯示所有 PostgreSQL 進程：

    ```bash
    ps aux | grep postgres
    ```

2. 終止所有 PostgreSQL 進程：

    ```bash
    sudo kill -9 <PID>
    ```

3. 刪除鎖文件：

    ```bash
    sudo rm /tmp/.s.PGSQL.5432.lock
    ```

4. 等待片刻後重新啟動 PostgreSQL 伺服器：

    ```bash
    pg_ctl -D /usr/local/var/postgres restart
    ```

## 配置外部連接到 PostgreSQL 伺服器

1. 編輯 `postgresql.conf` 文件：

    ```bash
    sudo nano /usr/local/var/postgres/postgresql.conf
    ```

    添加以下行：

    ```plaintext
    listen_addresses = '*'
    ```

2. 編輯 `pg_hba.conf` 文件：

    ```bash
    sudo nano /usr/local/var/postgres/pg_hba.conf
    ```

    添加以下行：

    ```plaintext
    host    all             all             0.0.0.0/0               md5
    ```

3. 創建 `pf` 規則文件：

    ```bash
    sudo nano /etc/pf.anchors/com.postgresql
    ```

    添加以下內容：

    ```plaintext
    rdr pass on en0 proto tcp from any to any port 5432 -> 127.0.0.1 port 5432
    ```

4. 編輯 `pf` 配置文件：

    ```bash
    sudo nano /etc/pf.conf
    ```

    添加以下行：

    ```plaintext
    anchor "com.postgresql"
    load anchor "com.postgresql" from "/etc/pf.anchors/com.postgresql"
    ```

5. 啟用 `pf` 規則：

    ```bash
    sudo pfctl -f /etc/pf.conf
    sudo pfctl -e
    ```

6. 重啟 PostgreSQL 伺服器：

    ```bash
    pg_ctl -D /usr/local/var/postgres restart
    ```

## 關閉 PostgreSQL 伺服器

```bash
pg_ctl -D /usr/local/var/postgres stop
```

## 啟動地端 API 伺服器

```bash
poetry run python heroku_app.py
```

## 確認 API 是否關閉

```bash
lsof -i :5001
```