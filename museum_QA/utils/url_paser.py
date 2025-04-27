

from urllib.parse import urlparse


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


if __name__ == "__main__":
    # Example usage
    url = "https://www.example.com"
    print(is_valid_url(url))  # Output: True

    url = "http: //not a url"
    print(is_valid_url(url))  # Output: False
