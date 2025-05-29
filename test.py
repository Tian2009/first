#!/usr/bin/env python3
import os
import sys
import json
import uuid
import random
import string
import subprocess
import datetime
import urllib.parse
from pathlib import Path

# 检查和安装依赖
def check_dependencies():
    print("检查依赖...")
    
    # 安装必要的系统包
    try:
        # 先检查系统类型
        if os.path.exists("/etc/debian_version"):
            # Debian/Ubuntu系统
            subprocess.run(["apt", "update"], check=True)
            
            # 检查pip
            try:
                subprocess.run(["which", "pip3"], check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print("安装pip3...")
                subprocess.run(["apt", "install", "-y", "python3-pip"], check=True)
                
            # 检查UFW
            try:
                subprocess.run(["which", "ufw"], check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print("安装UFW...")
                subprocess.run(["apt", "install", "-y", "ufw"], check=True)
                
        elif os.path.exists("/etc/redhat-release"):
            # CentOS/RHEL系统
            try:
                subprocess.run(["which", "pip3"], check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print("安装pip3...")
                subprocess.run(["yum", "install", "-y", "python3-pip"], check=True)
                
            # 检查UFW
            try:
                subprocess.run(["which", "ufw"], check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print("安装UFW...")
                subprocess.run(["yum", "install", "-y", "ufw"], check=True)
    except Exception as e:
        print(f"安装系统依赖失败: {e}")
    
    # 检查Python库
    missing_libs = []
    
    try:
        import qrcode
    except ImportError:
        missing_libs.append("qrcode[pil]")
    
    if missing_libs:
        print("缺少必要的Python库，尝试安装...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages"] + missing_libs, check=True)
            print("依赖安装成功")
        except subprocess.CalledProcessError as e:
            print(f"安装{', '.join(missing_libs)}库失败: {e}")
            print(f"请手动安装: pip install --break-system-packages {' '.join(missing_libs)}")
            return False
    
    return True

# 检查是否已安装sing-box
def check_singbox():
    try:
        result = subprocess.run(["sing-box", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"已检测到sing-box，当前版本: {version}")
            return True, version
        return False, None
    except FileNotFoundError:
        return False, None

# 安装sing-box
def install_singbox(version_type="stable", specific_version=None):
    print("开始安装sing-box...")
    
    if version_type == "stable":
        cmd = "curl -fsSL https://sing-box.app/install.sh | sh"
    elif version_type == "beta":
        cmd = "curl -fsSL https://sing-box.app/install.sh | sh -s -- --beta"
    elif version_type == "specific" and specific_version:
        cmd = f"curl -fsSL https://sing-box.app/install.sh | sh -s -- --version {specific_version}"
    else:
        print("无效的版本类型")
        return False
        
    try:
        subprocess.run(cmd, shell=True, check=True)
        print("sing-box安装成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装失败: {e}")
        return False

# 卸载sing-box
def uninstall_singbox():
    print("\n准备卸载sing-box...")
    confirm = input("确认卸载sing-box? 这将删除所有配置文件 (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("取消卸载")
        return False
    
    try:
        # 停止服务
        print("停止sing-box服务...")
        subprocess.run(["systemctl", "stop", "sing-box"], check=False)
        
        # 禁用服务
        print("禁用sing-box服务...")
        subprocess.run(["systemctl", "disable", "sing-box"], check=False)
        
        # 删除sing-box可执行文件
        print("删除sing-box程序...")
        subprocess.run(["rm", "-f", "/usr/local/bin/sing-box"], check=False)
        
        # 删除配置目录
        print("删除配置文件...")
        subprocess.run(["rm", "-rf", "/etc/sing-box"], check=False)
        
        # 删除服务文件
        print("删除服务文件...")
        subprocess.run(["rm", "-f", "/etc/systemd/system/sing-box.service"], check=False)
        
        # 重新加载系统服务
        subprocess.run(["systemctl", "daemon-reload"], check=False)
        
        print("sing-box已成功卸载")
        return True
    except Exception as e:
        print(f"卸载过程中出错: {e}")
        return False

# 启动服务
def start_service():
    try:
        subprocess.run(["systemctl", "start", "sing-box"], check=True)
        print("sing-box服务已启动")
    except subprocess.CalledProcessError as e:
        print(f"启动失败: {e}")

# 重启服务
def restart_service():
    try:
        subprocess.run(["systemctl", "restart", "sing-box"], check=True)
        print("sing-box服务已重启")
    except subprocess.CalledProcessError as e:
        print(f"重启失败: {e}")

# 停止服务
def stop_service():
    try:
        subprocess.run(["systemctl", "stop", "sing-box"], check=True)
        print("sing-box服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"停止失败: {e}")

# 生成随机字符串
def random_string(length=8):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# 获取服务器IP
def get_server_ip():
    try:
        result = subprocess.run(["curl", "-s", "https://api.ipify.org"], capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return "请手动填写服务器IP"

# 生成Reality密钥对
def generate_reality_keypair():
    try:
        result = subprocess.run(["sing-box", "generate", "reality-keypair"], 
                              capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        private_key = lines[0].split(': ')[1]
        public_key = lines[1].split(': ')[1]
        return private_key, public_key
    except Exception as e:
        print(f"生成Reality密钥对失败: {e}")
        # 如果失败，返回空字符串
        return "", ""

# 生成short_id
def generate_short_id():
    try:
        result = subprocess.run(["openssl", "rand", "-hex", "4"], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"生成short_id失败: {e}")
        # 如果失败，使用随机字符串
        return random_string(4)

# 创建自签证书
def create_self_signed_cert(domain="www.speedtest.net", cert_dir="/etc/sing-box/cert"):
    os.makedirs(cert_dir, exist_ok=True)
    cert_file = f"{cert_dir}/cert.pem"
    key_file = f"{cert_dir}/key.pem"
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print(f"证书已存在于 {cert_dir}")
        return cert_file, key_file
    
    print(f"为域名 {domain} 创建自签证书...")
    
    cmd = [
        "openssl", "req", "-x509", "-newkey", "rsa:2048", 
        "-keyout", key_file, "-out", cert_file,
        "-days", "3650", "-nodes", "-subj", f"/CN={domain}"
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"证书已创建: {cert_file}, {key_file}")
        return cert_file, key_file
    except subprocess.CalledProcessError as e:
        print(f"创建证书失败: {e}")
        return None, None

# 管理UFW端口
def manage_ufw_port(port, action="allow"):
    # 检查UFW状态
    try:
        result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
        status = "inactive"
        if "Status: active" in result.stdout:
            status = "active"
        
        if status == "inactive" and action == "allow":
            print("警告: UFW未启用，端口可能已经开放")
            
        if action == "allow":
            try:
                subprocess.run(["ufw", "allow", str(port)], check=True)
                print(f"端口 {port} 已开放")
                return True
            except subprocess.CalledProcessError as e:
                print(f"开放端口失败: {e}")
                return False
        elif action == "delete":
            try:
                subprocess.run(["ufw", "delete", "allow", str(port)], check=True)
                print(f"端口 {port} 已关闭")
                return True
            except subprocess.CalledProcessError as e:
                print(f"关闭端口失败: {e}")
                return False
        else:
            print("无效的操作")
            return False
    except Exception as e:
        print(f"UFW操作失败: {e}")
        return False

# 在终端中显示二维码
def display_terminal_qrcode(url):
    try:
        import qrcode
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(url)
        qr.make(fit=True)
        
        # 直接调用print_ascii显示二维码
        qr.print_ascii(invert=True)
    except ImportError:
        print("无法显示二维码：缺少qrcode库")
    except Exception as e:
        print(f"显示二维码失败: {e}")

# 生成二维码图片
def generate_qrcode_image(url, username, node_name="", save_dir="/tmp/qrcode"):
    try:
        import qrcode
        from PIL import Image
        
        # 创建保存目录
        os.makedirs(save_dir, exist_ok=True)
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 生成文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        node_name = node_name.replace(" ", "_") if node_name else username
        filename = f"{save_dir}/{username}_{node_name}_{timestamp}.png"
        
        # 保存图片
        img.save(filename)
        print(f"二维码已保存到 {filename}")
        return filename
    except Exception as e:
        print(f"生成二维码图片失败: {e}")
        return None

# 生成VLESS URL
def generate_vless_url(info, node_name=None):
    uuid_str = info.get("uuid", "")
    server_ip = info.get("server_ip", get_server_ip())
    port = info.get("port", 18890)
    flow = info.get("flow", "xtls-rprx-vision")
    security = "reality"
    sni = info.get("sni", "www.speedtest.net")
    fp = info.get("fp", "chrome")
    pbk = info.get("pbk", "")
    sid = info.get("sid", "")
    
    # URL编码参数
    encoded_node_name = urllib.parse.quote(node_name) if node_name else ""
    
    # 生成URL
    url = f"vless://{uuid_str}@{server_ip}:{port}?encryption=none&flow={flow}&security={security}&sni={sni}&fp={fp}&pbk={pbk}&sid={sid}&type=tcp&headerType=none&host={sni}#{encoded_node_name}"
    return url

# 生成Hysteria2 URL
def generate_hysteria2_url(info, node_name=None):
    password = info.get("password", "")
    server_ip = info.get("server_ip", get_server_ip())
    port = info.get("port", 443)
    sni = info.get("sni", "www.speedtest.net")
    insecure = "1" if info.get("insecure", True) else "0"
    
    # URL编码参数
    encoded_password = urllib.parse.quote(password)
    encoded_node_name = urllib.parse.quote(node_name) if node_name else ""
    
    # 生成URL
    url = f"hysteria2://{encoded_password}@{server_ip}:{port}?sni={sni}&alpn=h3,h2,http/1.1&obfs=salamander&obfs-password=ZXCZ123%40%21&insecure={insecure}#{encoded_node_name}"
    return url

# 从配置中获取用户信息
def get_users_from_config(config):
    users_info = {}
    server_ip = get_server_ip()
    
    # 获取Reality公钥
    reality_pubkey = ""
    for inbound in config["inbounds"]:
        if inbound.get("type") == "vless" and inbound.get("tls", {}).get("reality"):
            reality_pubkey = inbound["tls"]["reality"].get("public_key", "")
            break
    
    # 获取VLESS用户
    for inbound in config["inbounds"]:
        if inbound.get("type") == "vless":
            for user in inbound.get("users", []):
                username = user.get("name")
                if username:
                    users_info[username] = users_info.get(username, {})
                    users_info[username]["uuid"] = user.get("uuid")
                    users_info[username]["vless_port"] = inbound.get("listen_port")
                    
                    # 生成VLESS URL
                    short_id = inbound["tls"]["reality"].get("short_id", [""])[0] if isinstance(inbound["tls"]["reality"].get("short_id"), list) else inbound["tls"]["reality"].get("short_id", "")
                    sni = inbound["tls"]["reality"].get("server_name", "www.speedtest.net")
                    fp = inbound["tls"]["reality"].get("fingerprint", "chrome")
                    flow = user.get("flow", "xtls-rprx-vision")
                    
                    vless_url = generate_vless_url({
                        "uuid": user.get("uuid"),
                        "server_ip": server_ip,
                        "port": inbound.get("listen_port"),
                        "sni": sni,
                        "fp": fp,
                        "pbk": reality_pubkey,
                        "sid": short_id,
                        "flow": flow
                    }, username)
                    users_info[username]["vless_url"] = vless_url
    
    # 获取Hysteria2用户
    for inbound in config["inbounds"]:
        if inbound.get("type") == "hysteria2":
            for user in inbound.get("users", []):
                username = user.get("name")
                if username and username in users_info:
                    users_info[username]["hy2_password"] = user.get("password")
                    users_info[username]["hy2_port"] = inbound.get("listen_port")
                    
                    # 生成Hysteria2 URL
                    sni = inbound.get("tls", {}).get("server_name", "www.speedtest.net")
                    insecure = inbound.get("tls", {}).get("insecure", True)
                    
                    hy2_url = generate_hysteria2_url({
                        "password": user.get("password"),
                        "server_ip": server_ip,
                        "port": inbound.get("listen_port"),
                        "sni": sni,
                        "insecure": insecure
                    }, username)
                    users_info[username]["hysteria2_url"] = hy2_url
    
    return users_info

# 配置sing-box
def config_singbox():
    # 创建配置目录
    config_dir = Path("/etc/sing-box")
    config_dir.mkdir(exist_ok=True)
    cert_dir = Path("/etc/sing-box/cert")
    cert_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.json"
    
    # 检查是否有现有配置
    if config_file.exists():
        print(f"检测到现有配置文件: {config_file}")
        choice = input("是否覆盖现有配置? (y/n): ").strip().lower()
        if choice != 'y':
            print("保留现有配置")
            return
    
    # 获取用户信息
    username = input("请输入新用户名: ").strip()
    if not username:
        print("用户名不能为空")
        return
    
    # 获取端口信息
    while True:
        try:
            vless_port = input("请输入VLESS端口 (默认为18890): ").strip()
            vless_port = int(vless_port) if vless_port else 18890
            break
        except ValueError:
            print("请输入有效的端口号")
    
    while True:
        try:
            hy2_port = input("请输入Hysteria2端口 (默认为443): ").strip()
            hy2_port = int(hy2_port) if hy2_port else 443
            break
        except ValueError:
            print("请输入有效的端口号")
    
    # 生成配置所需的变量
    user_uuid = str(uuid.uuid4())
    private_key, public_key = generate_reality_keypair()
    short_id = generate_short_id()
    hy2_password = random_string(16)
    server_name = "www.speedtest.net"
    
    # 创建自签证书
    cert_file, key_file = create_self_signed_cert(domain=server_name)
    
    print("\n正在生成配置文件...")
    
    # 配置模板
    config = {
        "inbounds": [
            {
                "type": "vless",
                "listen": "::",
                "listen_port": vless_port,
                "users": [
                    {
                        "name": username,
                        "uuid": user_uuid,
                        "flow": "xtls-rprx-vision"
                    }
                ],
                "tls": {
                    "enabled": True,
                    "server_name": server_name,
                    "reality": {
                        "enabled": True,
                        "handshake": {
                            "server": server_name,
                            "server_port": 443
                        },
                        "private_key": private_key,
                        "short_id": [short_id],
                        "max_time_difference": "12h"
                    }
                }
            },
            {
                "type": "hysteria2", 
                "tag": "hy2-in",
                "listen": "::",
                "listen_port": hy2_port,
                "up_mbps": 1000,
                "down_mbps": 1000,
                "obfs": {
                    "type": "salamander",
                    "password": "ZXCZ123@!"
                },
                "users": [
                    {
                        "name": username,
                        "password": hy2_password
                    }
                ],
                "ignore_client_bandwidth": False,
                "tls": {
                    "enabled": True,
                    "server_name": "www.speedtest.net",
                    "certificate_path": cert_file,
                    "key_path": key_file,
                    "alpn": ["h3", "http/1.1"]
                },
                "masquerade": "https://www.speedtest.net",
                "brutal_debug": False
            }
        ],
        "outbounds": [
            {
                "type": "direct"
            },
            {
                "type": "block",
                "tag": "block"
            }
        ]
    }
    
    # 保存配置文件
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print(f"配置文件已保存到 {config_file}")
    
    # 保存密钥信息到单独文件方便查看
    keys_file = cert_dir / "keys.json"
    keys_info = {
        "reality": {
            "private_key": private_key,
            "public_key": public_key,
            "short_id": short_id
        }
    }
    
    with open(keys_file, 'w') as f:
        json.dump(keys_info, f, indent=4)
    
    print(f"密钥信息已保存到 {keys_file}")
    
    # 开放防火墙端口
    manage_ufw_port(vless_port)
    manage_ufw_port(hy2_port)
    
    # 重启服务
    restart_service()
    
    # 生成连接URL
    server_ip = get_server_ip()
    
    vless_url = generate_vless_url({
        "uuid": user_uuid,
        "server_ip": server_ip,
        "port": vless_port,
        "sni": server_name,
        "fp": "chrome",
        "pbk": public_key,
        "sid": short_id
    }, username)
    
    hy2_url = generate_hysteria2_url({
        "password": hy2_password,
        "server_ip": server_ip,
        "port": hy2_port,
        "sni": server_name,
        "insecure": True
    }, username)
    
    # 显示连接信息
    print("\n=== 连接信息 ===")
    print(f"VLESS链接: {vless_url}")
    display_terminal_qrcode(vless_url)
    generate_qrcode_image(vless_url, username, "VLESS")
    
    print(f"\nHysteria2链接: {hy2_url}")
    display_terminal_qrcode(hy2_url)
    generate_qrcode_image(hy2_url, username, "Hysteria2")

# 列出用户
def list_users():
    config_file = Path("/etc/sing-box/config.json")
    if not config_file.exists():
        print("配置文件不存在")
        return
        
    # 读取配置
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    users_info = get_users_from_config(config)
    
    if not users_info:
        print("未找到用户信息")
        return
    
    print("\n=== 用户列表 ===")
    for username, info in users_info.items():
        print(f"\n用户名: {username}")
        
        if "vless_url" in info:
            print(f"VLESS链接: {info['vless_url']}")
            display_terminal_qrcode(info['vless_url'])
            generate_qrcode_image(info['vless_url'], username, "VLESS")
        
        if "hysteria2_url" in info:
            print(f"\nHysteria2链接: {info['hysteria2_url']}")
            display_terminal_qrcode(info['hysteria2_url'])
            generate_qrcode_image(info['hysteria2_url'], username, "Hysteria2")

# 添加用户
def add_user():
    config_file = Path("/etc/sing-box/config.json")
    if not config_file.exists():
        print("配置文件不存在，请先配置sing-box")
        return
    
    # 读取配置
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # 检查配置格式
    vless_inbound = None
    hy2_inbound = None
    
    for inbound in config["inbounds"]:
        if inbound.get("type") == "vless":
            vless_inbound = inbound
        elif inbound.get("type") == "hysteria2":
            hy2_inbound = inbound
    
    if not vless_inbound or not hy2_inbound:
        print("现有配置无效，找不到VLESS或Hysteria2入站")
        return
    
    # 获取用户信息
    username = input("请输入新用户名: ").strip()
    if not username:
        print("用户名不能为空")
        return
    
    # 检查用户名是否已存在
    for user in vless_inbound.get("users", []):
        if user.get("name") == username:
            print("用户名已存在")
            return
    
    # 生成UUID和密码
    user_uuid = str(uuid.uuid4())
    hy2_password = random_string(16)
    
    # 获取节点名称
    node_name = input("请输入节点名称 (默认与用户名相同): ").strip()
    if not node_name:
        node_name = username
    
    # 添加到VLESS配置
    new_vless_user = {
        "name": username,
        "uuid": user_uuid,
        "flow": "xtls-rprx-vision"
    }
    vless_inbound["users"].append(new_vless_user)
    
    # 添加到Hysteria2配置
    new_hy2_user = {
        "name": username,
        "password": hy2_password
    }
    hy2_inbound["users"].append(new_hy2_user)
    
    # 保存配置
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)
    
    print("用户添加成功，重启服务...")
    restart_service()
    
    # 生成连接URL
    server_ip = get_server_ip()
    
    # 获取Reality参数
    reality_pubkey = ""
    short_id = ""
    server_name = "www.speedtest.net"
    
    if "tls" in vless_inbound and "reality" in vless_inbound["tls"]:
        reality = vless_inbound["tls"]["reality"]
        server_name = vless_inbound["tls"].get("server_name", server_name)
        
        # 读取公钥
        keys_file = Path("/etc/sing-box/cert/keys.json")
        if keys_file.exists():
            with open(keys_file, 'r') as f:
                keys = json.load(f)
                reality_pubkey = keys.get("reality", {}).get("public_key", "")
        
        if not reality_pubkey:
            print("警告: 找不到Reality公钥，生成的URL可能不正确")
        
        short_id = reality.get("short_id", [""])[0] if isinstance(reality.get("short_id"), list) else reality.get("short_id", "")
        
    vless_url = generate_vless_url({
        "uuid": user_uuid,
        "server_ip": server_ip,
        "port": vless_inbound.get("listen_port"),
        "sni": server_name,
        "fp": "chrome",
        "pbk": reality_pubkey,
        "sid": short_id
    }, node_name)
    
    hy2_insecure = True
    if "tls" in hy2_inbound:
        hy2_insecure = hy2_inbound["tls"].get("insecure", True)
        server_name = hy2_inbound["tls"].get("server_name", server_name)
    
    hy2_url = generate_hysteria2_url({
        "password": hy2_password,
        "server_ip": server_ip,
        "port": hy2_inbound.get("listen_port"),
        "sni": server_name,
        "insecure": hy2_insecure
    }, node_name)
    
    # 显示连接信息
    print("\n=== 连接信息 ===")
    print(f"VLESS链接: {vless_url}")
    display_terminal_qrcode(vless_url)
    generate_qrcode_image(vless_url, username, node_name + "_VLESS")
    
    print(f"\nHysteria2链接: {hy2_url}")
    display_terminal_qrcode(hy2_url)
    generate_qrcode_image(hy2_url, username, node_name + "_Hysteria2")

# 删除用户
def delete_user():
    config_file = Path("/etc/sing-box/config.json")
    if not config_file.exists():
        print("配置文件不存在")
        return
        
    # 读取配置
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # 查找入站
    vless_inbound = None
    hy2_inbound = None
    
    for inbound in config["inbounds"]:
        if inbound.get("type") == "vless":
            vless_inbound = inbound
        elif inbound.get("type") == "hysteria2":
            hy2_inbound = inbound
    
    if not vless_inbound or not hy2_inbound:
        print("现有配置无效")
        return
        
    # 获取用户列表
    users = []
    for user in vless_inbound.get("users", []):
        if "name" in user:
            users.append(user["name"])
    
    if not users:
        print("没有找到用户")
        return
        
    print("\n=== 用户列表 ===")
    for i, username in enumerate(users, 1):
        print(f"{i}. {username}")
        
    # 选择用户
    try:
        choice = int(input("\n请选择要删除的用户编号 (0返回): "))
        if choice == 0:
            return
        if choice < 1 or choice > len(users):
            print("无效的选择")
            return
            
        target_user = users[choice - 1]
        
        # 确认删除
        confirm = input(f"确认删除用户 {target_user}? (y/n): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return
            
        # 删除VLESS用户
        vless_inbound["users"] = [u for u in vless_inbound.get("users", []) if u.get("name") != target_user]
        
        # 删除Hysteria2用户
        hy2_inbound["users"] = [u for u in hy2_inbound.get("users", []) if u.get("name") != target_user]
        
        # 保存配置
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
            
        print(f"用户 {target_user} 已删除")
        
        # 检查是否需要关闭端口
        if not vless_inbound["users"]:
            # 没有用户了，可以关闭端口
            manage_ufw_port(vless_inbound["listen_port"], "delete")
        
        if not hy2_inbound["users"]:
            # 没有用户了，可以关闭端口
            manage_ufw_port(hy2_inbound["listen_port"], "delete")
        
        # 重启服务
        restart_service()
        
    except ValueError:
        print("请输入有效的数字")
    except Exception as e:
        print(f"操作失败: {e}")

# 修改用户信息
def modify_user():
    config_file = Path("/etc/sing-box/config.json")
    if not config_file.exists():
        print("配置文件不存在")
        return
        
    # 读取配置
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    users_info = get_users_from_config(config)
    if not users_info:
        print("未找到用户信息")
        return
        
    print("\n=== 现有用户列表 ===")
    for idx, (username, info) in enumerate(users_info.items(), 1):
        print(f"{idx}. {username}")
    
    try:
        user_idx = int(input("\n请选择要修改的用户编号: ").strip()) - 1
        if user_idx < 0 or user_idx >= len(users_info):
            print("无效的用户编号")
            return
            
        selected_username = list(users_info.keys())[user_idx]
        
        print(f"\n=== 修改用户: {selected_username} ===")
        print("1. 修改UUID")
        print("2. 修改Hysteria2密码")
        print("3. 修改节点名称")
        print("0. 返回")
        
        mod_choice = input("\n请选择要修改的信息 [0-3]: ").strip()
        
        if mod_choice == "1":
            new_uuid = str(uuid.uuid4())
            print(f"新UUID: {new_uuid}")
            if input("确认修改? (y/n): ").lower() == 'y':
                # 更新VLESS用户的UUID
                for inbound in config["inbounds"]:
                    if inbound.get("type") == "vless":
                        for user in inbound.get("users", []):
                            if user.get("name") == selected_username:
                                user["uuid"] = new_uuid
                                break
                
                # 保存配置并重启服务
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                    
                print(f"用户{selected_username}的UUID已更新")
                restart_service()
                
                # 更新并显示新链接
                users_info = get_users_from_config(config)
                print(f"\n新的连接信息:")
                user_info = users_info.get(selected_username)
                if user_info:
                    if "vless_url" in user_info:
                        print(f"VLESS链接: {user_info['vless_url']}")
                        display_terminal_qrcode(user_info['vless_url'])
                        generate_qrcode_image(user_info['vless_url'], selected_username, "VLESS")
                        
        elif mod_choice == "2":
            new_password = input("请输入新的Hysteria2密码 (留空将随机生成): ").strip()
            if not new_password:
                new_password = random_string(16)
            print(f"新密码: {new_password}")
            
            if input("确认修改? (y/n): ").lower() == 'y':
                # 更新Hysteria2用户密码
                for inbound in config["inbounds"]:
                    if inbound.get("type") == "hysteria2":
                        for user in inbound.get("users", []):
                            if user.get("name") == selected_username:
                                user["password"] = new_password
                                break
                
                # 保存配置并重启服务
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                    
                print(f"用户{selected_username}的Hysteria2密码已更新")
                restart_service()
                
                # 更新并显示新链接
                users_info = get_users_from_config(config)
                print(f"\n新的连接信息:")
                user_info = users_info.get(selected_username)
                if user_info:
                    if "hysteria2_url" in user_info:
                        print(f"Hysteria2链接: {user_info['hysteria2_url']}")
                        display_terminal_qrcode(user_info['hysteria2_url'])
                        generate_qrcode_image(user_info['hysteria2_url'], selected_username, "Hysteria2")
                        
        elif mod_choice == "3":
            new_name = input("请输入新的节点名称: ").strip()
            if not new_name:
                print("节点名称不能为空")
                return
                
            # 保存节点名称到配置的自定义字段
            node_name_file = Path("/etc/sing-box/node_names.json")
            node_names = {}
            if node_name_file.exists():
                try:
                    with open(node_name_file, 'r') as f:
                        node_names = json.load(f)
                except:
                    pass
            
            node_names[selected_username] = new_name
            
            with open(node_name_file, 'w') as f:
                json.dump(node_names, f, indent=4)
                
            print(f"节点名称已更新为: {new_name}")
            
            # 重新生成链接
            server_ip = get_server_ip()
            reality_pubkey = ""
            short_id = ""
            
            # 获取VLESS信息
            vless_port = None
            vless_uuid = None
            vless_sni = "www.speedtest.net"
            
            # 获取Hysteria2信息
            hy2_port = None
            hy2_password = None
            hy2_sni = "www.speedtest.net"
            hy2_insecure = True
            
            # 从配置中读取信息
            for inbound in config["inbounds"]:
                if inbound.get("type") == "vless":
                    for user in inbound.get("users", []):
                        if user.get("name") == selected_username:
                            vless_uuid = user.get("uuid")
                            vless_port = inbound.get("listen_port")
                            if "tls" in inbound:
                                vless_sni = inbound["tls"].get("server_name", vless_sni)
                                if "reality" in inbound["tls"]:
                                    reality = inbound["tls"]["reality"]
                                    short_id = reality.get("short_id", [""])[0] if isinstance(reality.get("short_id"), list) else reality.get("short_id", "")
                                    
                                    # 读取公钥
                                    keys_file = Path("/etc/sing-box/cert/keys.json")
                                    if keys_file.exists():
                                        with open(keys_file, 'r') as f:
                                            keys = json.load(f)
                                            reality_pubkey = keys.get("reality", {}).get("public_key", "")
                            break
                
                elif inbound.get("type") == "hysteria2":
                    for user in inbound.get("users", []):
                        if user.get("name") == selected_username:
                            hy2_password = user.get("password")
                            hy2_port = inbound.get("listen_port")
                            if "tls" in inbound:
                                hy2_sni = inbound["tls"].get("server_name", hy2_sni)
                                hy2_insecure = inbound["tls"].get("insecure", hy2_insecure)
                            break
            
            # 生成新链接
            if vless_uuid and vless_port:
                vless_url = generate_vless_url({
                    "uuid": vless_uuid,
                    "server_ip": server_ip,
                    "port": vless_port,
                    "sni": vless_sni,
                    "fp": "chrome",
                    "pbk": reality_pubkey,
                    "sid": short_id
                }, new_name)
                
                print(f"\nVLESS链接: {vless_url}")
                display_terminal_qrcode(vless_url)
                generate_qrcode_image(vless_url, selected_username, new_name + "_VLESS")
            
            if hy2_password and hy2_port:
                hy2_url = generate_hysteria2_url({
                    "password": hy2_password,
                    "server_ip": server_ip,
                    "port": hy2_port,
                    "sni": hy2_sni,
                    "insecure": hy2_insecure
                }, new_name)
                
                print(f"\nHysteria2链接: {hy2_url}")
                display_terminal_qrcode(hy2_url)
                generate_qrcode_image(hy2_url, selected_username, new_name + "_Hysteria2")
                
        elif mod_choice == "0":
            return
        else:
            print("无效选择")
            
    except ValueError:
        print("请输入有效的数字")
    except Exception as e:
        print(f"修改用户信息失败: {e}")

# 更新用户URL信息
def update_user_urls(config, users_info):
    server_ip = get_server_ip()
    
    # 获取Reality公钥
    reality_pubkey = ""
    keys_file = Path("/etc/sing-box/cert/keys.json")
    if keys_file.exists():
        try:
            with open(keys_file, 'r') as f:
                keys = json.load(f)
                reality_pubkey = keys.get("reality", {}).get("public_key", "")
        except:
            pass
    
    # 获取节点名称
    node_name_file = Path("/etc/sing-box/node_names.json")
    node_names = {}
    if node_name_file.exists():
        try:
            with open(node_name_file, 'r') as f:
                node_names = json.load(f)
        except:
            pass
    
    # 更新所有用户的URL
    for username, info in users_info.items():
        # 获取节点名称
        node_name = node_names.get(username, username)
        
        # 更新VLESS URL
        for inbound in config["inbounds"]:
            if inbound.get("type") == "vless":
                for user in inbound.get("users", []):
                    if user.get("name") == username:
                        if "tls" in inbound and "reality" in inbound["tls"]:
                            short_id = inbound["tls"]["reality"].get("short_id", [""])[0] if isinstance(inbound["tls"]["reality"].get("short_id"), list) else inbound["tls"]["reality"].get("short_id", "")
                            sni = inbound["tls"].get("server_name", "www.speedtest.net")
                            fp = inbound["tls"]["reality"].get("fingerprint", "chrome")
                            
                            vless_url = generate_vless_url({
                                "uuid": user.get("uuid"),
                                "server_ip": server_ip,
                                "port": inbound.get("listen_port"),
                                "sni": sni,
                                "fp": fp,
                                "pbk": reality_pubkey,
                                "sid": short_id,
                                "flow": user.get("flow", "xtls-rprx-vision")
                            }, node_name)
                            info["vless_url"] = vless_url
        
        # 更新Hysteria2 URL
        for inbound in config["inbounds"]:
            if inbound.get("type") == "hysteria2":
                for user in inbound.get("users", []):
                    if user.get("name") == username:
                        sni = inbound.get("tls", {}).get("server_name", "www.speedtest.net")
                        insecure = inbound.get("tls", {}).get("insecure", True)
                        
                        hy2_url = generate_hysteria2_url({
                            "password": user.get("password"),
                            "server_ip": server_ip,
                            "port": inbound.get("listen_port"),
                            "sni": sni,
                            "insecure": insecure
                        }, node_name)
                        info["hysteria2_url"] = hy2_url

# 管理防火墙
def manage_firewall():
    # 检查UFW状态
    try:
        result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
        status = "inactive"
        if "Status: active" in result.stdout:
            status = "active"
    except Exception as e:
        print(f"获取UFW状态失败: {e}")
        status = "unknown"
    
    while True:
        print("\n=== 防火墙管理 ===")
        print(f"当前状态: {status}")
        print("1. 启用防火墙")
        print("2. 禁用防火墙")
        print("3. 打开端口")
        print("4. 关闭端口")
        print("0. 返回上级菜单")
        
        choice = input("\n请选择操作 [0-4]: ").strip()
        
        if choice == "1":
            if status == "active":
                print("UFW防火墙已经处于启用状态")
            else:
                try:
                    subprocess.run(["ufw", "--force", "enable"], check=True)
                    print("UFW防火墙已启用")
                    status = "active"
                except subprocess.CalledProcessError as e:
                    print(f"启用防火墙失败: {e}")
        
        elif choice == "2":
            if status == "inactive":
                print("UFW防火墙已经处于禁用状态")
            else:
                try:
                    subprocess.run(["ufw", "--force", "disable"], check=True)
                    print("UFW防火墙已禁用")
                    status = "inactive"
                except subprocess.CalledProcessError as e:
                    print(f"禁用防火墙失败: {e}")
        
        elif choice == "3":
            try:
                port = int(input("请输入要打开的端口: ").strip())
                manage_ufw_port(port, "allow")
            except ValueError:
                print("请输入有效的端口号")
        
        elif choice == "4":
            try:
                port = int(input("请输入要关闭的端口: ").strip())
                manage_ufw_port(port, "delete")
            except ValueError:
                print("请输入有效的端口号")
        
        elif choice == "0":
            return
        
        else:
            print("无效选择，请重试")
        
        input("\n按Enter键继续...")

# 管理sing-box
def manage_singbox():
    installed, version = check_singbox()
    
    while True:
        print("\n=== sing-box 管理 ===")
        if installed:
            print(f"当前版本: {version}")
            print("1. 查看 sing-box 状态")
            print("2. 查看 sing-box 日志")
            print("3. 启动 sing-box 服务")
            print("4. 重启 sing-box 服务") 
            print("5. 停止 sing-box 服务")
            print("6. 实时查看日志")
            print("7. 更新 sing-box")
            print("8. 卸载 sing-box")
        else:
            print("sing-box 未安装")
            print("1. 安装 sing-box (稳定版)")
            print("2. 安装 sing-box (测试版)")
            print("3. 安装指定版本")
        print("0. 返回上级菜单")
        
        choice = input("\n请选择操作: ").strip()
        
        if installed:
            if choice == "1":
                view_singbox_status()
            elif choice == "2":
                view_singbox_logs()
            elif choice == "3":
                start_service()
            elif choice == "4":
                restart_service()
            elif choice == "5":
                stop_service()
            elif choice == "6":
                print("\n=== 实时日志 (按Ctrl+C退出) ===")
                try:
                    subprocess.run(["journalctl", "-u", "sing-box", "-f"], check=True)
                except KeyboardInterrupt:
                    print("\n已退出日志查看")
                except Exception as e:
                    print(f"查看日志失败: {e}")
            elif choice == "7":
                print("\n=== 更新 sing-box ===")
                print("1. 更新到最新稳定版")
                print("2. 更新到最新测试版")
                print("3. 更新到指定版本")
                print("0. 返回")
                
                update_choice = input("\n请选择更新类型: ").strip()
                if update_choice == "1":
                    if install_singbox("stable"):
                        installed, version = check_singbox()
                elif update_choice == "2":
                    if install_singbox("beta"):
                        installed, version = check_singbox()
                elif update_choice == "3":
                    specific_version = input("请输入要安装的版本号 (例如 v1.5.0): ").strip()
                    if specific_version:
                        if install_singbox("specific", specific_version):
                            installed, version = check_singbox()
                elif update_choice == "0":
                    continue
                else:
                    print("无效选择")
            elif choice == "8":
                if uninstall_singbox():
                    installed = False
                    version = None
            elif choice == "0":
                return
            else:
                print("无效选择，请重试")
        else:
            if choice == "1":
                if install_singbox("stable"):
                    installed, version = check_singbox()
            elif choice == "2":
                if install_singbox("beta"):
                    installed, version = check_singbox()
            elif choice == "3":
                specific_version = input("请输入要安装的版本号 (例如 v1.5.0): ").strip()
                if specific_version:
                    if install_singbox("specific", specific_version):
                        installed, version = check_singbox()
            elif choice == "0":
                return
            else:
                print("无效选择，请重试")
        
        input("\n按Enter键继续...")

def view_singbox_status():
    print("\n=== sing-box 状态信息 ===")
    try:
        result = subprocess.run(["systemctl", "status", "sing-box"], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"获取状态失败: {e}")

def view_singbox_logs():
    print("\n=== sing-box 日志信息 ===")
    try:
        result = subprocess.run(["journalctl", "-u", "sing-box", "--no-pager", "-n", "50"], 
                               capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"获取日志失败: {e}")

# 用户管理子菜单
def manage_users():
    config_file = Path("/etc/sing-box/config.json")
    if not config_file.exists():
        print("配置文件不存在，请先配置sing-box")
        return
        
    while True:
        print("\n=== 用户管理 ===")
        print("1. 查看现有用户")
        print("2. 添加新用户")
        print("3. 删除用户")
        print("4. 修改用户信息")
        print("0. 返回上级菜单")
        
        choice = input("\n请选择操作 [0-4]: ").strip()
        
        if choice == "1":
            list_users()
        elif choice == "2":
            add_user()
        elif choice == "3":
            delete_user()
        elif choice == "4":
            modify_user()
        elif choice == "0":
            return
        else:
            print("无效选择，请重试")
        
        input("\n按Enter键继续...")

# 主函数
def main():
    if os.geteuid() != 0:
        print("此脚本需要root权限运行")
        sys.exit(1)
        
    try:
        if not check_dependencies():
            sys.exit(1)
            
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print("\n=== sing-box 安装配置工具 ===")
            
            installed, version = check_singbox()
            if installed:
                print(f"当前sing-box版本: {version}")
            else:
                print("sing-box未安装")
                
            print("1. sing-box 管理")
            print("2. 配置 sing-box")
            print("3. 用户管理")
            print("4. 防火墙管理")
            print("0. 退出")
            
            choice = input("\n请选择操作 [0-4]: ").strip()
            
            if choice == "1":
                manage_singbox()
            elif choice == "2":
                config_singbox()
            elif choice == "3":
                manage_users()
            elif choice == "4":
                manage_firewall()
            elif choice == "0":
                print("感谢使用，再见！")
                break
            else:
                print("无效选择，请重试")
            
            input("\n按Enter键继续...")
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
    
