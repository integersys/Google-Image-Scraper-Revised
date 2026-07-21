# Google Image Scraper

A Python tool that automates collecting and downloading images from Google Images.

If you are looking for other image scrapers, [JJLimmm's Website Image Scraper](https://github.com/JJLimmm/Website-Image-Scraper) supports Getty Images, Shutterstock, and Bing.

## Requirements

1. Google Chrome
2. Python 3
3. Python packages (Pillow, Selenium, and Requests)
4. Windows

Other operating systems may work but have not been fully tested.

## Setup

1. Open Command Prompt or PowerShell.
2. Clone the repository or download.

    ```bat
    git clone https://github.com/integersys/Google-Image-Scraper.git
    cd Google-Image-Scraper
    ```

3. Create the directory used by the automatic ChromeDriver downloader.

    ```bat
    mkdir webdriver
    ```

4. Install the required Python packages.

    ```bat
    python -m pip install -r requirements.txt
    ```

5. Edit the configuration values in `main.py`.
6. Run the scraper from the project directory.

    ```bat
    python main.py
    ```

The correct ChromeDriver is downloaded automatically when one is not already available in the `webdriver` directory.

## Configuration

The changable settings are located near the bottom of `main.py`.

| Setting | Description |
| --- | --- |
| `search_keys` | Search queries. Each query receives its own output directory. |
| `number_of_images` | Number of image URLs requested per query. The final number of saved files may be lower. |
| `headless` | Controls whether Chrome is visible. Visible mode is recommended because Google may block headless sessions. |
| `min_resolution` | Minimum accepted `(width, height)`. Smaller images are deleted after downloading. |
| `max_resolution` | Maximum accepted `(width, height)`. Larger images are deleted after downloading. |
| `max_missed` | Number of consecutive preview failures allowed before the current search stops. |
| `number_of_workers` | Number of simultaneous searches. One worker is recommended to reduce Google throttling. |
| `keep_filenames` | Preserves names from image URLs when `True`. Generated filenames are safer when `False`. |

Example configuration:

```python
search_keys = ["purple sports car -toy -drawing"]
number_of_images = 25
headless = False
min_resolution = (800, 600)
max_resolution = (6000, 6000)
max_missed = 15
number_of_workers = 1
keep_filenames = False
```

`number_of_images` applies to every query. Two queries with `number_of_images = 25` request up to 50 images in total.

Avoid using characters that Windows does not permit in directory names inside `search_keys`:

```text
< > : " / \ | ? *
```

## Output

Images are saved under a separate directory for each query:

```text
photos\<search query>\
```

For example:

```text
photos\stars\
```

The final file count can be lower than `number_of_images` because of:

- Failed or timed-out downloads
- Duplicate image URLs
- Unsupported or damaged images
- Minimum and maximum resolution filtering
- Google throttling or browser verification

## Google Consent and Verification

Google may display a consent dialog or redirect to an automated-traffic verification page. 

Keep `headless = False` if verification is required. Complete the check in the visible Chrome window and the scraper will resume automatically. The scraper waits up to three minutes for verification.

If verification is requested while `headless = True`, the scraper exits with a message asking you to use visible mode.

Occasional messages like this are expected:

```text
[INFO] Unable to get link
```

This means an individual result did not provide a usable full-resolution preview within the allowed time. A successful result resets the failure counter. The search stops only after `max_missed` consecutive failures.

## Compatibility Updates

The scraper has been updated to:

- Use Google's current image-search route
- Locate current image-result containers
- Retrieve full-resolution preview URLs
- Handle Google consent dialogs
- Detect automated-traffic verification
- Reduce Chrome automation and background-log noise
- Continue after isolated preview failures

## Credits

Original project by [OHyic](https://github.com/ohyicong/Google-Image-Scraper)
