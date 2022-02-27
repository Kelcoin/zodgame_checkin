# encoding=utf8
import io
import re
import sys
import time
import subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

def get_driver_version():
   cmd = r'''powershell -command "&{(Get-Item 'C:\Program Files\Google\Chrome\Application\chrome.exe').VersionInfo.ProductVersion}"'''
   try:
       out, err = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
       out = out.decode('utf-8').split(".")[0]
       return out
   except IndexError as e:
       print('Check chrome version failed:{}'.format(e))
       return 0

def zodgame_checkin(driver, formhash):
    checkin_url = "https://zodgame.xyz/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=0"    
    checkin_query = """
        (function (){
        var request = new XMLHttpRequest();
        var fd = new FormData();
        fd.append("formhash","%s");
        fd.append("qdxq","kx");
        request.open("POST","%s",false);
        request.withCredentials=true;
        request.send(fd);
        return request;
        })();
        """ % (formhash, checkin_url)
    checkin_query = checkin_query.replace("\n", "")
    driver.set_script_timeout(240)
    resp = driver.execute_script("return " + checkin_query)
    match = re.search('<div class="c">\n(.*?)</div>\n', resp["response"], re.S)
    message = match[1] if match is not None else "签到失败"
    print(f"【签到】{message}")
    return "恭喜你签到成功!" in message or "您今日已经签到，请明天再来" in message


def zodgame_task(driver, formhash):
    driver.get("https://zodgame.xyz/plugin.php?id=jnbux")
    WebDriverWait(driver, 240, 5).until(
        lambda x: x.title != "Just a moment..."
    )

    join_bux = driver.find_elements(By.XPATH, '//font[text()="开始参与任务"]')
    if len(join_bux) != 0 :    
        driver.get(f"https://zodgame.xyz/plugin.php?id=jnbux:jnbux&do=join&formhash={formhash}")
        WebDriverWait(driver, 240, 5).until(
            lambda x: x.title != "Just a moment..."
        )
        zodgame_task(driver, formhash)

    join_task_a = driver.find_elements(By.XPATH, '//a[text()="参与任务"]')
    success = True

    if len(join_task_a) == 0:
        print("【任务】所有任务均已完成。")
        return success

    for idx, a in enumerate(join_task_a):
        on_click = a.get_attribute("onclick")
        try:
            function = re.search("openNewWindow(.*)\(\);", on_click, re.S)[0]
            resp = driver.execute_script(function)
            driver.switch_to.window(driver.window_handles[-1])
            WebDriverWait(driver, 240, 5).until(
                lambda x: x.find_elements(By.XPATH, '//div[text()="成功！"]')
            )
            check_url = re.search('plugin.php(.*)page=0', on_click, re.S)[0]
            driver.get(f"https://zodgame.xyz/{check_url}")
            WebDriverWait(driver, 240, 5).until(
                lambda x: x.find_elements(By.XPATH, '//p[text()="检查成功, 积分已经加入您的帐户中"]')
            )
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            print(f"【任务】任务 {idx+1} 成功。")
        except:
            print(f"【任务】任务 {idx+1} 失败。")
            success = False
            continue
    return success

def zodgame(cookie_string):
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")
    #options.add_argument("--no-sandbox")
      
    version = get_driver_version()
    driver = uc.Chrome(version_main=version, options = options)

    # Load cookie
    driver.get("https://zodgame.xyz/")

    cookie_string = cookie_string.replace("/","%2")
    cookie_dict = [ 
        {"name" : x.split('=')[0].strip(), "value": x.split('=')[1].strip()} 
        for x in cookie_string.split(';')
    ]

    driver.delete_all_cookies()
    for cookie in cookie_dict:
        if cookie["name"] in ["qhMq_2132_saltkey", "qhMq_2132_auth"]:
            driver.add_cookie({
                "domain": "zodgame.xyz",
                "name": cookie["name"],
                "value": cookie["value"],
                "path": "/",
            })
    
    driver.get("https://zodgame.xyz/")
    
    try:
        WebDriverWait(driver, 240, 5).until(
            lambda x: x.title != "Just a moment..."
        )
        formhash = driver.find_element(By.XPATH, '//input[@name="formhash"]').get_attribute('value')
    except:
        assert False, "Login fails. Please check your cookie."
    
    assert zodgame_checkin(driver, formhash) and zodgame_task(driver, formhash), "Checkin failed or task failed."

    driver.close()
    driver.quit()
    
if __name__ == "__main__":
    cookie_string = sys.argv[1]
    assert cookie_string
    
    zodgame(cookie_string)
