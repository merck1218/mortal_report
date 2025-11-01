# mortal_report

## 検証済み環境
- Rocky Linux 9.6
- Nginx
- PostgreSQL

## OS基本設定
SELinux無効化
```bash
vi /etc/selinux/config
SELINUX=disabled

reboot
```

Firewalld無効化
```bash
systemctl stop firewalld
systemctl disable firewalld
```

ミドルウェアインストール(Git、tar)
```bash
dnf -y install git tar
```

## Nginx設定
Nginxインストール
```bash
dnf -y install nginx
```

Nginx設定(root部分とlocation部分を書き換える)
```bash
vi /etc/nginx/nginx.conf
server {
    # root         /usr/share/nginx/html;
    location / {
        alias /app/mortal_report/frontend/dist/;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /killerducky/ {
            alias /app/mortal_report/killerducky/killerducky/;
            try_files $uri $uri/ /index.html;
    }

    location /report/ {
            alias /app/mortal_report/killerducky/report/;
            try_files $uri $uri/ /index.html;
    }
```

Nginx起動および自動起動設定
```bash
systemctl start nginx
systemctl enable nginx
```

## PostgreSQL設定
PostgreSQLインストール
```bash
dnf -y install https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm
dnf -y install postgresql18-server
```

PostgreSQL初期設定
```bash
su - postgres
/usr/pgsql-18/bin/initdb
exit
```

PostgreSQL起動および自動起動設定
```bash
systemctl start postgresql-18
systemctl enable postgresql-18
```

## Node.js設定
Node.jsインストール
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
\. "$HOME/.nvm/nvm.sh"
nvm install 22
```

Node.jsインストール結果確認
```bash
node -v
⇒v22.x.xと表示される

npm -v
⇒10.x.xと表示される
```

## Python-pip設定
pipインストール
```bash
dnf -y install python3-pip
```

pipインストール結果確認
```bash
pip -V
⇒pip 21.x.xと表示される
```

## Mortal Report設定
Mortal Reportインストール
```bash
mkdir /app
git clone https://github.com/merck1218/mortal_report.git
```

初期データ登録
```bash
su - postgres
psql

CREATE DATABASE mahjong;
CREATE USER mahjong WITH PASSWORD '<パスワード>';
ALTER DATABASE mahjong OWNER TO mahjong;
exit

psql -U mahjong -d mahjong -h 127.0.0.1 -f /app/mortal_report/backend/initial_data_setup.sql
exit
```

Mortal Reportフロントエンド設定
```bash
cd /app/mortal_report/frontend
npm install

vi .env
VITE_API_BASE_URL=http://<Your IP or Your Hostname>

npm run dev -- --host
⇒エラーが表示されないこと、「http://<Your IP or Your Hostname>:5173/top」にアクセスし画面が表示されることを確認
Ctrl + Cで終了

npm build
```

Mortal Reportバックエンド設定
```bash
cd /app/mortal_report/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

vi .env
DATABASE_URL=postgresql://mahjong:<パスワード>@127.0.0.1:5432/mahjong
SERVER_HOST=<Your IP or Your Hostname>
DST_PATH=/app/mortal-report/killerducky/report/

python run.py
```

KillerDucky設定(https://github.com/killerducky/killer_mortal_gui?tab=readme-ov-file)
```bash
cd /app/mortal_report/killerducky
git clone https://github.com/killerducky/killer_mortal_gui.git
mv mv killer_mortal_gui killerducky
```

## 最終方法
「http://Your IP or Your Hostname/top」にアクセスし、トップページが表示されることを確認する
