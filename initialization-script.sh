#!/bin/bash
# 初始化学生作业批改系统

# 显示帮助信息的函数
show_help() {
    echo "学生作业批改系统初始化脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help          显示此帮助信息"
    echo "  -d, --dev           以开发模式初始化系统"
    echo "  -p, --prod          以生产模式初始化系统"
    echo "  -t, --test          以测试模式初始化系统"
    echo "  --with-docker       使用Docker初始化系统"
    echo "  --with-sample-data  初始化时添加示例数据"
    echo ""
    echo "示例:"
    echo "  $0 --dev --with-sample-data  # 以开发模式初始化并添加示例数据"
    echo "  $0 --prod                    # 以生产模式初始化"
    echo ""
}

# 默认配置
FLASK_ENV="development"
USE_DOCKER=false
WITH_SAMPLE_DATA=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--dev)
            FLASK_ENV="development"
            ;;
        -p|--prod)
            FLASK_ENV="production"
            ;;
        -t|--test)
            FLASK_ENV="testing"
            ;;
        --with-docker)
            USE_DOCKER=true
            ;;
        --with-sample-data)
            WITH_SAMPLE_DATA=true
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    shift
done

echo "=== 学生作业批改系统初始化 ==="
echo "环境: $FLASK_ENV"
echo "使用Docker: $USE_DOCKER"
echo "添加示例数据: $WITH_SAMPLE_DATA"
echo ""

# 检查是否存在 Python 虚拟环境
check_venv() {
    if [ -d "venv" ]; then
        echo "[√] 已存在虚拟环境"
    else
        echo "[!] 创建虚拟环境..."
        python -m venv venv
        echo "[√] 虚拟环境创建成功"
    fi
}

# 安装依赖
install_dependencies() {
    echo "[!] 安装依赖..."
    if [ "$USE_DOCKER" = true ]; then
        echo "[i] 跳过依赖安装，将在Docker中安装"
    else
        source venv/bin/activate
        pip install -r requirements.txt
        echo "[√] 依赖安装成功"
    fi
}

# 创建配置文件
create_config() {
    if [ ! -f ".env" ]; then
        echo "[!] 创建配置文件..."
        cp .env.example .env
        
        # 生成随机密钥
        if command -v openssl &> /dev/null; then
            SECRET_KEY=$(openssl rand -hex 24)
            sed -i "s/your-secret-key-here/$SECRET_KEY/g" .env
        fi
        
        echo "[√] 配置文件创建成功"
    else
        echo "[√] 配置文件已存在"
    fi
}

# 初始化数据库
init_database() {
    echo "[!] 初始化数据库..."
    if [ "$USE_DOCKER" = true ]; then
        echo "[i] 将在Docker中初始化数据库"
    else
        source venv/bin/activate
        export FLASK_APP=manage.py
        export FLASK_ENV=$FLASK_ENV
        
        flask db init
        flask db migrate -m "Initial migration"
        flask db upgrade
        
        if [ "$WITH_SAMPLE_DATA" = true ]; then
            echo "[!] 添加示例数据..."
            flask init_db
            echo "[√] 示例数据添加成功"
        fi
        
        echo "[√] 数据库初始化成功"
    fi
}

# 创建管理员用户
create_admin() {
    if [ "$USE_DOCKER" = true ]; then
        echo "[i] 跳过管理员创建，将在Docker中创建"
    else
        echo "[!] 创建管理员用户..."
        source venv/bin/activate
        export FLASK_APP=manage.py
        export FLASK_ENV=$FLASK_ENV
        
        read -p "管理员用户名: " admin_username
        read -p "管理员邮箱: " admin_email
        read -s -p "管理员密码: " admin_password
        echo ""
        
        flask create_admin --username "$admin_username" --email "$admin_email" --password "$admin_password"
        echo "[√] 管理员用户创建成功"
    fi
}

# 使用Docker初始化
init_with_docker() {
    echo "[!] 使用Docker初始化系统..."
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        echo "[×] Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose是否安装
    if ! command -v docker-compose &> /dev/null; then
        echo "[×] Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 创建Nginx配置目录
    mkdir -p nginx
    
    # 创建Nginx配置文件
    if [ ! -f "nginx/nginx.conf" ]; then
        echo "[!] 创建Nginx配置文件..."
        cat > nginx/nginx.conf << 'EOL'
server {
    listen 80;
    server_name localhost;

    # 日志配置
    access_log /var/log/nginx/app_access.log;
    error_log /var/log/nginx/app_error.log;

    # 静态文件缓存设置
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # 上传文件目录
    location /static/uploads/ {
        alias /usr/share/nginx/html/static/uploads/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Flask应用代理
    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        client_max_body_size 16M;
    }

    # 健康检查
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOL
        echo "[√] Nginx配置文件创建成功"
    fi
    
    # 创建logs目录
    mkdir -p logs
    
    # 构建并启动Docker容器
    echo "[!] 构建并启动Docker容器..."
    docker-compose up -d
    
    # 等待容器启动
    echo "[!] 等待容器启动..."
    sleep 5
    
    # 初始化数据库
    echo "[!] 初始化数据库..."
    docker-compose exec web flask db upgrade
    
    if [ "$WITH_SAMPLE_DATA" = true ]; then
        echo "[!] 添加示例数据..."
        docker-compose exec web flask init_db
        echo "[√] 示例数据添加成功"
    else
        # 创建管理员用户
        echo "[!] 创建管理员用户..."
        read -p "管理员用户名: " admin_username
        read -p "管理员邮箱: " admin_email
        read -s -p "管理员密码: " admin_password
        echo ""
        
        docker-compose exec web flask create_admin --username "$admin_username" --email "$admin_email" --password "$admin_password"
        echo "[√] 管理员用户创建成功"
    fi
    
    echo "[√] Docker初始化成功"
    echo ""
    echo "系统已启动，请访问 http://localhost 使用"
}

# 主函数
main() {
    # 检查必要文件是否存在
    if [ ! -f "requirements.txt" ] || [ ! -f "manage.py" ]; then
        echo "[×] 缺少必要文件，请确保在项目根目录下运行"
        exit 1
    fi
    
    if [ "$USE_DOCKER" = true ]; then
        create_config
        init_with_docker
    else
        check_venv
        install_dependencies
        create_config
        init_database
        create_admin
        
        echo ""
        echo "初始化完成，可以通过以下命令启动应用："
        echo "  source venv/bin/activate"
        echo "  export FLASK_APP=manage.py"
        echo "  export FLASK_ENV=$FLASK_ENV"
        echo "  flask run"
    fi
    
    echo ""
    echo "=== 学生作业批改系统初始化完成 ==="
}

# 执行主函数
main
