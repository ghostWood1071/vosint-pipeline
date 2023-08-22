from playwright.sync_api import sync_playwright
import time

def select(from_element, expr, by = "css="):
        element = from_element.locator(f"{by}{expr}")
        element = [element.nth(i) for i in range(element.count())]
        return element
def crawl_ttxvn(username,password,id_news):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto('https://news.vnanet.vn/')
            page.click('#btnSignIn')

            page.fill('#username', username)
            page.fill('#password', password)

            page.click('#login')
            time.sleep(1)
            

            page.goto('https://news.vnanet.vn/FrontEnd/PostDetail.aspx?id='+ str(id_news))
            content = select(page,".post-content")[0].inner_text()
        except:
            page.close()
    
    return content
    
