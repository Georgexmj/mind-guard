from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 冯奶奶的密码哈希
hash = '$2b$12$MYLExfWD2SoK4B8EY276x.dGMsG2J67SlYnAf7Y8mg6rFVYfaf2ey'

# 测试常见密码
test_passwords = ['123456', '12345678', 'password', 'admin', 'elder', '111111']

for pwd in test_passwords:
    if pwd_context.verify(pwd, hash):
        print(f'密码是: {pwd}')
        break
else:
    print('没有找到匹配的密码')