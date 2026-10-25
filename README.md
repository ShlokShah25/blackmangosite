# Black Mango — website redesign prototype

A clickable redesign of [blackmangoobjects.com](https://blackmangoobjects.com): black-and-mango look, welcome animation, the full catalogue, custom rug requests, and a try-in-your-room tool for every product.

## Deploy
`index.html` is the whole site in one file (images embedded). Deploy the repo root as a static site on Vercel, Netlify, Cloudflare Pages or GitHub Pages. No build step.

## Edit
- Page markup, styles and scripts: `source/site.html`
- Product images: `source/assets/`
- Rebuild `index.html` after editing: `python3 source/build.py`

## Prototype notes
Cart, checkout and forms work on the page only; nothing is sent anywhere. Real orders and messages arrive when this is rebuilt as the store's Shopify theme.
