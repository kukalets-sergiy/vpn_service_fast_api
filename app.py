from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
from urllib.parse import urljoin, urlparse

app = FastAPI()

# Dictionary to map site names to their base URLs
SITES = {
    "Terrikon": "https://terrikon.com",
    "Korrespondent": "https://ua.korrespondent.net/",
    "othersite": "https://example.com",
    "Rozetka": "https://rozetka.com.ua/ua/",
    "Techdefinc": "https://techdefinc.com/",
    # Add more sites here as needed
}


@app.get("/", response_class=HTMLResponse)
async def home():
    # Generates a simple home page listing available sites
    site_links = "\n".join(f'<li><a href="/{site}/{urlparse(url).netloc}/">{site}</a></li>' for site, url in SITES.items())
    return f"<h1>Available Sites</h1><ul>{site_links}</ul>"


@app.get("/{site_name}/{domain}/{routes_on_original_site:path}", response_class=HTMLResponse)
async def proxy(site_name: str, domain: str, routes_on_original_site: str, request: Request):
    target_url_base = SITES.get(site_name)

    if not target_url_base:
        return HTMLResponse(content="Site not found", status_code=404)

    # Extract the domain from the target URL base
    parsed_url = urlparse(target_url_base)
    actual_domain = parsed_url.netloc

    # Ensure the domain in the path matches the actual domain of the target URL
    if domain != actual_domain:
        return HTMLResponse(content="Invalid domain in the URL", status_code=400)

    if not domain.endswith('/'):
        domain += '/'

    # Construct the full target URL by ensuring there is a "/" after the domain if needed
    if not routes_on_original_site.startswith('/'):
        routes_on_original_site = '/' + routes_on_original_site

    # Construct the full target URL
    target_url = urljoin(target_url_base, routes_on_original_site)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(target_url, params=request.query_params)
        except httpx.RequestError as exc:
            return HTMLResponse(content=f"Error fetching {target_url}: {exc}", status_code=500)

    proxy_base_url = f"http://localhost:8000/{site_name}/{domain}"
    content = response.text.replace(target_url_base, proxy_base_url)

    # Adjust relative links to ensure they include the site name and domain
    content_lines = content.splitlines()
    for i, line in enumerate(content_lines):
        if 'src="' in line or 'href="' in line:
            parts = line.split('"')
            """
            The even indices (0, 2, 4, ...) contain the text outside the quotes. 
            The odd indices (1, 3, 5, ...) contain the URLs or values inside the quotes.
            <img src="https://example.com/image.png">
            '<img src=',                     # index 0 (text before first ")
            'https://example.com/image.png', # index 1 (URL inside first ")
            """
            for j in range(1, len(parts), 2):
                """
                This loop iterates over the indices of parts, starting from index 1 and stepping by 2.
                This means it processes only the odd indices, which correspond to the URLs extracted from the src or
                href attributes.                
                """
                # For each odd index, this line retrieves the URL stored in that part of the list.
                url = parts[j]
                if urlparse(url).scheme in ('http', 'https'):
                    continue
                new_url = urljoin(proxy_base_url, url)
                """
                urljoin does not automatically modify paths that start with / to include any additional
                segments (like a site name or domain)
                """
                if url.startswith('/'):
                    # Ensure the site_name and domain are included for relative paths
                    url_prefix = f"/{site_name}/{domain}"
                    new_url = url_prefix.rstrip('/') + "/" + url.lstrip('/')
                parts[j] = new_url
            content_lines[i] = '"'.join(parts)

    modified_content = "\n".join(content_lines)

    return HTMLResponse(content=modified_content, status_code=response.status_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


















