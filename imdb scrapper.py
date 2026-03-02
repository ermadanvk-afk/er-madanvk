from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def handle_cookie_popup(driver):
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'accept')]"))
        )
        accept_button.click()
        print("Cookie popup handled")
        time.sleep(1)
    except TimeoutException:
        print("No cookie popup detected")
    except Exception as e:
        print(f"Cookie popup handling: {e}")

def load_more_reviews(driver, num_clicks=5):
    print(f"\n seeing more reviews ({num_clicks} clicks)")

    for i in range(num_clicks):
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'ipc-see-more__button') or contains(text(), 'Load More')]"))
            )

            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            time.sleep(2)
            load_more_button.click()
            print(f"Click {i+1}/{num_clicks} completed")
            time.sleep(2)
        except TimeoutException:
            print(f"No more 'Load More' button found after {i} clicks")
            break
        except Exception as e:
            print(f"Error on click {i+1}: {e}")
            break

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

def extract_reviews(soup):
    reviews_data = []
    review_containers = soup.find_all('div', class_='review-container')

    if not review_containers:
        review_containers = soup.find_all('article', class_=lambda x: x and 'user-review' in x.lower() if x else False)

    if not review_containers:
        review_containers = soup.find_all('div', attrs={'data-testid': lambda x: x and 'review' in x.lower() if x else False})

    for idx, container in enumerate(review_containers, 1):
        try:
            title_elem = container.find('a', class_='title') or \
                        container.find('h3') or \
                        container.find('span', class_=lambda x: x and 'title' in x.lower() if x else False)
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            review_text = container.find("div",class_="ipc-html-content-inner-div").text.strip()

            rating_elem = container.find('span', class_=lambda x: x and 'rating' in x.lower() if x else False) or \
                         container.find('span', attrs={'class': lambda x: x and 'ipc-rating-star' in x if x else False})

            rating = None
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)

                rating = ''.join(filter(lambda x: x.isdigit() or x == '.', rating_text.split('/')[0]))
                rating = rating if rating else None

            reviews_data.append({
                'title': title,
                'review_text': review_text,
                'rating': rating
            })

        except Exception as e:
            continue

    return reviews_data

def scrape_imdb_reviews(url, num_load_more_clicks=5):
    driver = None

    try:
        print("Starting IMDb Reviews Scraper")
        print(f"URL: {url}\n")

        driver = setup_driver()

        print("Loading IMDb reviews page...")
        driver.get(url)
        time.sleep(3)

        handle_cookie_popup(driver)

        load_more_reviews(driver, num_load_more_clicks)

        soup = BeautifulSoup(driver.page_source, 'lxml')

        reviews = extract_reviews(soup)

        df = pd.DataFrame(reviews)

        csv_filename = 'imdb_reviews.csv'
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        return df

    except Exception as e:
        return None

    finally:
        if driver:
            driver.quit()
            print("\nBrowser closed")
url = "https://www.imdb.com/title/tt33014583/reviews/?ref_=tt_ov_ururv"

df = scrape_imdb_reviews(url, num_load_more_clicks=5)
print(df)