import re

from bs4 import BeautifulSoup


def get_html_meta_tags(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.title.string if soup.title else None
    
    if title:
        title = title.strip().replace("\n", " ")
    
    meta_description = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_description["content"] if meta_description else None
    
    meta_url = soup.find("meta", attrs={"property": "og:url"})
    meta_url = meta_url["content"] if meta_url else None
    
    meta_image = soup.find("meta", attrs={"property": "og:image"})
    meta_image = meta_image["content"] if meta_image else None
    
    meta_name = soup.find("meta", attrs={"property": "og:site_name"})
    
    meta_name = meta_name["content"] if meta_name else None
    if meta_name:
        meta_name = meta_name.strip().replace("\n", " ")
    
    return {
        "title": title,
        "meta_description": meta_description,
        "meta_url": meta_url,
        "meta_image": meta_image,
        "meta_name": meta_name
    }


def get_homepage_meta_image(site):
    homepage = site.root_page.specific
    
    if homepage and hasattr(homepage, "get_meta_image"):
        return homepage.get_meta_image()
    
    return None


def get_homepage_meta_description(site):
    homepage = site.root_page.specific
    
    if homepage and hasattr(homepage, "get_meta_description"):
        return homepage.get_meta_description()
    
    return None
