# Room try-on for the Black Mango Shopify theme

Adds "View in your room" to product pages. Customers upload a photo of their room, or use a sample room, and see the piece placed there:

- Rugs lie flat on the floor.
- Cushions sit on the sofa.
- Pedestals and objects stand on the floor.
- Glassware stands on a table.

Customers can drag, pinch, resize, rotate or flip the piece, add it to the cart, and save or share the picture. The room photo is processed in the browser and is never uploaded.

Nothing else in the theme changes. Work on a **duplicate of the live theme** first, then publish once it looks right.

## 1. Add the theme files

In **Online Store › Themes › … › Edit code**, add these four files with the same names. You can also push them with the Shopify CLI or GitHub sync.

| Folder | File |
|---|---|
| `sections/` | `bm-room-tryon.liquid` |
| `snippets/` | `bm-tryon-item.liquid` |
| `assets/` | `bm-room-tryon.js` |
| `assets/` | `bm-room-tryon.css` |

Optional: `templates/page.room-tryon.json` adds a standalone "Try in your room" page.

## 2. Upload the try-on pictures

The try-on needs a picture of each product **with no background**. The files are in `tryon-images/`, named `tryon-<product-handle>.png`.

Upload all of them in **Content › Files**. Keep the file names exactly as they are, because the section finds each picture by its name.

If a product has no picture there, the try-on falls back to the product's main photo, which will show its background. To use a different picture for one product, create a product metafield `custom.tryon_image` (type: file, image) and set it on that product. The metafield takes priority over the file name.

## 3. Turn it on for product pages

1. Go to **Customize › Products › Default product › Add section › Room try-on**.
2. Place it right under the product information. It shows a "View in your room" button that opens the try-on full screen, with that product already selected.

To put the button inside the product info instead, for example under Add to cart:

1. Add a **Custom Liquid** block there containing:
   ```html
   <button type="button" class="button" data-bmto-trigger>View in your room</button>
   ```
2. In the Room try-on section, turn off **Show the button in this section**.

## 4. Optional: a standalone page

Create a page called "Try in your room", give it the template `page.room-tryon`, and link it from the menu.

## Settings

| Setting | What it does |
|---|---|
| Heading and text | Title and introduction shown above the try-on. |
| Products to offer | Choose a collection, or leave it empty to offer every product. |
| Button and Add to cart labels and colours | Match these to the theme. |

The try-on decides where each product goes from its **product type**: types containing "rug" go on the floor, "cushion" on the sofa, and "glass" on a table; everything else stands on the floor. To override this for one product, create a product metafield `custom.tryon_placement` (single-line text) with the value `floor`, `sofa`, `stand` or `table`.

## Notes

- **Cart.** Add to cart posts to the store's own `/cart/add.js` and then fires a `cart:refresh` event. If the theme's cart drawer or cart count doesn't update straight away, hook that event to the theme's cart refresh.
- **Picture quality.** The supplied cut-outs were made from the images on the live site. For sharper results, cut them again from the original product photos (any PNG with a transparent background works) and re-upload them with the same names.
- **Demo.** `demo/index.html` runs the try-on with sample data. Serve this folder over HTTP to try it.

## Floating video

The looping silhouette videos are in `../videos/`:

- 16:9 (1920×1080) and 4:5 (1080×1350)
- MP4 and WebM, 12-second seamless loops, all under 1 MB

Upload them to the theme's video section or to Content › Files. If you embed them by hand, use:

```html
<video autoplay muted loop playsinline poster="">
  <source src="black-mango-floating-16x9.webm" type="video/webm">
  <source src="black-mango-floating-16x9.mp4" type="video/mp4">
</video>
```
