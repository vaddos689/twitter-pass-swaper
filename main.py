import asyncio
from loguru import logger

from better_automation.twitter.errors import HTTPException as TwitterException
from better_automation.utils import proxy_session, write_lines, load_lines
from better_automation.twitter import (
    Account as TwitterAccount,
    Client as TwitterClient,
    errors as twitter_errors,
)


async def start_swapper(auth_token: str, proxy: str, password: str, old_password: str):
    account = TwitterAccount(auth_token)
    proxy_url = f'http://{proxy}'

    async with proxy_session(proxy_url) as session:
        twitter = TwitterClient(account, session)

        try:
            await twitter.request_user_data()
            print(f"[{account.short_auth_token}] {account.data}")

            swap_password_status = await twitter.swap_password(password=password, old_password=old_password)
            if swap_password_status:
                cookies = twitter.session.cookie_jar.filter_cookies('https://twitter.com/')
                for key, cookie in cookies.items():
                    print('Key: "%s", Value: "%s"' % (cookie.key, cookie.value))

                    if cookie.value == 'auth_token':
                        print(f"auth_token: {cookie.value}")
                        new_auth_token = cookie.value

                with open('new_datas.txt', 'a') as file:
                    file.write(f'{password}:{new_auth_token}\n')

                logger.success(f'{account.short_auth_token} succes')

            else:
                logger.error(f'error request with | {account.short_auth_token}')

        except twitter_errors.HTTPException as exc:
            logger.error(f"Не удалось выполнить запрос. Статус аккаунта: {account.status.value}")
            raise exc


async def main(auth_tokens: list, proxies: list, passwords: list, old_passwords: list):
    for i in range(len(auth_tokens)):
        await start_swapper(auth_token=auth_tokens[i], proxy=proxies[i], password=passwords[i], old_password=old_passwords[i])


if __name__ == '__main__':
    print('Откуда брать данные для аккаунта?\n')

    with open('proxies.txt', "r") as file:
        proxies = [row.strip() for row in file]

    with open('new_passwords.txt', "r") as file:
        passwords = [row.strip() for row in file]

    with open('current_passwords.txt', "r") as file:
        old_passwords = [row.strip() for row in file]

    user_action: int = int(input('\n1. Из файла json_cookies.txt'
                                 '\n2. Из файла auth_tokens.txt'
                                 '\nВыберите ваше действие: '))

    print('')

    match user_action:
        case 1:
            accounts = TwitterAccount.from_file("json_cookies.txt", cookies=True)
            auth_tokens = [acc.auth_token for acc in accounts]
            asyncio.run(main(auth_tokens=auth_tokens, proxies=proxies, passwords=passwords, old_passwords=old_passwords))

        case 2:
            accounts = TwitterAccount.from_file("auth_tokens.txt")
            auth_tokens = [acc.auth_token for acc in accounts]
            asyncio.run(main(auth_tokens=auth_tokens, proxies=proxies, passwords=passwords, old_passwords=old_passwords))

        case _:
            pass
