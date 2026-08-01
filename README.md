# Climbers Heaven Guide

A comprehensive climbing route guide application featuring interactive maps, multi-language support, and offline access via Progressive Web App (PWA) technology. This project combines reStructuredText (RST) documentation with a modern Svelte-based web frontend to create an engaging climbing destination guide.

## 🏔️ Project Overview

Climbers Heaven Guide is a documentation and web application project that transforms detailed climbing route descriptions (written in RST format) into an interactive, interactive web application. It covers climbing destinations across Montenegro and surrounding areas, featuring:

- **Interactive Maps**: Geo-located climbing areas with custom markers
- **Route Information**: Detailed climbing route descriptions with grades, statistics, and guides
- **Multi-Language Support**: Content available in English, German, and Serbian
- **Offline Access**: PWA support for use without internet connectivity
- **Responsive Design**: Mobile-friendly interface optimized for all devices

## 🏗️ Architecture Overview

The project follows a three-tier architecture:

```text
Content Layer (docutil/)
        ↓ Python Compilation (scripts/compile_guide.py)
        ↓
Intermediate Layer (Static JSON/HTML)
        ↓ Vite Build (html/)
        ↓
Web Frontend (Svelte + Vite)
```

### Layer 1: Content Layer (`docutil/`)

- **RST (reStructuredText) source files** documenting climbing routes and areas
- **Custom docutils directives** for maps, geolocation markers, and route statistics
- **KML file** for geographic data and marker definitions
- **Images and media** (AVIF format for optimized delivery)
- Language variants: `guide.rst` (English), `guide-de.rst` (German)

### Layer 2: Compilation Layer (`scripts/`)

- **`compile_guide.py`**: Main build script that:
  - Parses RST files using docutils
  - Applies custom Climbers Heaven directives
  - Generates SVG topos and graphics
  - Produces static JSON and HTML output
  - Optimizes and embeds images
- Supporting scripts for scraping route data, managing images, and editing

### Layer 3: Web Frontend (`html/`)

- **Svelte Kit**: Modern reactive framework with static site generation
- **Vite**: Lightning-fast build tool
- **Tailwind CSS**: Utility-first styling with custom theme
- **i18n (Lingui)**: Internationalization framework for multi-language support
- **PWA Support**: Service worker for offline functionality

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Content** | reStructuredText (RST) | Write climbing route documentation |
| **Compilation** | Python 3, docutils | Transform RST → JSON/HTML |
| **Graphics** | SVG elements, PIL/Pillow | Generate topos and images |
| **Geo** | fastkml, KML | Geographic data and markers |
| **Frontend** | Svelte, SvelteKit | Reactive UI framework |
| **Build** | Vite | Fast bundling and dev server |
| **Styling** | Tailwind CSS | Utility-first CSS framework |
| **i18n** | Lingui | Multi-language support (en, de, sr) |
| **PWA** | Vite PWA | Offline capability and installation |
| **Package Management** | npm (frontend), conda/pip (backend) | Dependency management |

## 📁 Project Structure

```text
climbers-heaven-guide/
├── docutil/                          # Content layer: RST source files
│   ├── guide.rst                     # Main English guide
│   ├── guide-de.rst                  # German guide
│   ├── Climbersheaven.kml            # Geographic markers and regions
│   ├── background.avif               # UI background images
│   └── [regions]/                    # Regional climbing guides
│       ├── bar/                      # Bar region (Menke, Stari Bar, Župci)
│       ├── durmitor/                 # Durmitor mountain region
│       ├── kolasin/                  # Kola šin region
│       └── podgorica/                # Podgorica area
│           ├── lovka/                # Lovka sector (largest)
│           ├── smokovac/             # Smokovac sector
│           ├── cijevna/              # Cijevna river canyon
│           ├── dementia/             # Dementia sector
│           ├── seliste/              # Seliš te sector
│           ├── titograd/             # Titograd sector
│           └── wonderwall/           # Wonderwall sector
│
├── scripts/                          # Compilation layer: Build scripts
│   ├── compile_guide.py              # Main compilation script (RST → JSON)
│   ├── images.py                     # Image processing and optimization
│   ├── crags-scraper.py              # Scrape route data from external sources
│   ├── eightanu_scraper.py           # Specific scraper for eightanu.com
│   ├── edit.py                       # Utility for editing guide content
│   ├── kompass.svg                   # Compass rose graphic
│   └── season.svg                    # Season indicator graphic
│
├── html/                             # Frontend layer: Web application
│   ├── src/
│   │   ├── app.html                  # HTML entry point
│   │   ├── app.css                   # Global styles
│   │   ├── app.d.ts                  # TypeScript definitions
│   │   ├── routes/
│   │   │   ├── +layout.svelte        # Main layout component
│   │   │   └── +page.svelte          # Home page
│   │   ├── lib/                      # Reusable components
│   │   │   ├── Layout.svelte         # Layout wrapper
│   │   │   ├── Menu.svelte           # Navigation menu
│   │   │   ├── MapTools.svelte       # Map controls
│   │   │   ├── *.coffee              # CoffeeScript utilities (zoom, overview, tools)
│   │   │   └── svg/                  # SVG components
│   │   ├── locales/                  # Internationalization
│   │   │   ├── en.po, en.ts          # English (en) translations
│   │   │   ├── de.po, de.ts          # German (de) translations
│   │   │   └── sr.po, sr.ts          # Serbian (sr) translations
│   │   └── static/
│   │       ├── data/
│   │       │   ├── guide.json        # Compiled guide data
│   │       │   ├── guide.txt         # Text version
│   │       │   └── img/              # Static images
│   │       └── robots.txt
│   ├── build/                        # Production build output
│   ├── dev-dist/                     # Development build output
│   ├── climbers-heaven-theme/        # Custom Skeleton UI theme
│   ├── package.json                  # npm dependencies and scripts
│   ├── svelte.config.js              # SvelteKit configuration
│   ├── vite.config.js                # Vite configuration
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   ├── lingui.config.js              # i18n configuration
│   └── jsconfig.json                 # JavaScript project configuration
│
└── README.md                         # This file
```

## 📋 Prerequisites

### Backend (Content Compilation)

- **Conda** or **pip** for Python package management
- **Python 3.8+**
- See [scripts/compile_guide.py](scripts/compile_guide.py) for specific Python packages:
  - `docutils` — RST parsing and processing
  - `Pillow` — Image manipulation
  - `svgelements` — SVG creation and manipulation
  - `drawsvg` — Draw route topo SVG overlays
  - `pillow-avif-plugin` — AVIF image codec support for Pillow
  - `defusedxml` — Safe XML parser required for Pillow XMP metadata reading
  - `fastkml` — KML/KMZ geographic data
  - `levenshtein` — String similarity for scraping
  - `minify-html` — HTML minification (`htmlmin` is not compatible with Python 3.13+)

### Frontend (Web Application)

- **Node.js 18+** and **npm 9+** (or yarn/pnpm)
- Modern web browser for testing

## 🚀 Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd /path/to/climbers-heaven-guide
```

### 2. Install Python Dependencies

Using conda (recommended):

```bash
conda install docutils Pillow svgelements
pip install drawsvg pillow-avif-plugin defusedxml fastkml levenshtein minify-html
```

Or using pip directly:

```bash
pip install docutils Pillow svgelements drawsvg pillow-avif-plugin defusedxml fastkml levenshtein minify-html
```

### 3. Install Frontend Dependencies

```bash
cd html
npm install
cd ..
```

### 4. Verify Installation

Test the Python environment:

```bash
cd scripts
python compile_guide.py
cd ..
```

This should generate compiled guide data in `html/static/data/`.

## 🔨 Build Process

### Compilation Workflow

The build process consists of two main stages:

#### Stage 1: Content Compilation (Python)

```bash
cd scripts
python compile_guide.py
```

**What it does:**

1. Reads RST source files from `docutil/`
2. Parses custom Climbers Heaven directives (geomap, geolocation, routestatistics)
3. Generates SVG graphics for route topos
4. Optimizes and embeds images
5. Outputs JSON data structure to `html/static/data/guide.json`
6. Generates text version to `html/static/data/guide.txt`

**Inputs:**

- `docutil/guide.rst` — Main English content
- `docutil/guide-de.rst` — German translations
- `docutil/Climbersheaven.kml` — Geographic markers
- `docutil/[regions]/*.rst` — Regional climbing guides
- Images in AVIF format

**Outputs:**

- `html/static/data/guide.json` — Structured climbing data
- `html/static/data/guide.txt` — Plain text export
- `html/static/data/img/` — Optimized images

#### Stage 2: Frontend Build (Vite + Svelte)

```bash
cd html
npm run build
```

**What it does:**

1. Runs SvelteKit prerendering
2. Compiles Svelte components to JavaScript
3. Processes CSS with Tailwind
4. Bundles with Vite for optimization
5. Generates PWA assets and service worker
6. Outputs production-ready site to `build/`

**Configuration:**

- `svelte.config.js` — Static site adapter, prerender settings
- `vite.config.js` — Vite bundler configuration
- `tailwind.config.js` — CSS framework configuration
- `lingui.config.js` — i18n compilation

## 💻 Development Workflow

### Start Development Server

```bash
cd html
npm run dev
```

This starts a hot-reload development server (typically at `http://localhost:5173`).

### Full Development Cycle

1. **Edit content** — Modify RST files in `docutil/`
2. **Compile guide** — Run `python scripts/compile_guide.py`
3. **View changes** — Refresh browser or restart dev server
4. **Check code** — Run linting and type checking

### Useful npm Scripts

```bash
cd html

# Development
npm run dev              # Start dev server with hot reload
npm run build            # Build for production
npm run preview          # Preview production build locally

# Code Quality
npm run check            # Type-check Svelte components
npm run check:watch      # Watch for type errors
npm run lint             # Check code formatting
npm run format           # Auto-format code with Prettier

# i18n & Testing
npm run extract          # Extract translatable strings
npm run compile          # Compile translations to TypeScript
npm test                 # Run unit tests with Vitest
```

### Editing Guide Content

1. **Add/Edit climbing routes** in `docutil/[region]/[sector].rst`
2. **Update German translations** in `docutil/guide-de.rst`
3. **Modify geographic markers** in `docutil/Climbersheaven.kml`
4. **Add images** to `docutil/[region]/pics/` (use AVIF format)
5. **Recompile** with `python scripts/compile_guide.py`
6. **Test locally** with `npm run dev` in `html/`

See [docutil/readme.md](docutil/readme.md) for detailed documentation on custom RST directives and formatting.

## 📜 Custom RST Directives

Climbers Heaven uses custom docutils directives for enhanced functionality:

### `.. geomap::`

Displays an interactive map showing climbing area locations.

```rst
.. geomap::
    :levels: 1
    :folder: None
```

Parameters:

- `levels` — Depth of location collection (0 = current section only, 1+ includes subsections)
- `folder` — KML folder name to display markers from

### `.. geolocation::`

Marks a specific climbing location on the map.

```rst
.. geolocation::
    :coords: 42.0931, 19.1002
    :marker: MarkerName
    :show-title: 0
    :direction: nw
```

Parameters:

- `coords` — Latitude, longitude pair
- `marker` — Name of KML marker
- `show-title` — Zoom level when title appears (0 = never)
- `direction` — Title position (nw, n, ne, e, se, s, sw, w)

### `.. routestatistics::`

Displays a bar chart of climbing grades for routes in following sections.

```rst
.. routestatistics::
```

See [docutil/readme.md](docutil/readme.md) for complete directive documentation.

## 🌍 Internationalization (i18n)

The project supports multiple languages using the Lingui framework:

### Supported Languages

- **English** (en) — Primary language
- **German** (de) — German translations
- **Serbian** (sr) — Serbian translations

### Adding Translations

1. **Mark translatable strings** in Svelte components:

   ```svelte
   <h1>{i18n._('guides.title')}</h1>
   ```

2. **Extract strings** to translation files:

   ```bash
   npm run extract
   ```

3. **Add translations** to `src/locales/[lang].po`

4. **Compile translations** to TypeScript:

   ```bash
   npm run compile
   ```

### Translation Files

- `src/locales/en.po` / `en.ts` — English
- `src/locales/de.po` / `de.ts` — German
- `src/locales/sr.po` / `sr.ts` — Serbian

## 🏭 Key Scripts

### `compile_guide.py`

**Purpose:** Main build script transforming RST content to JSON

**Usage:**

```bash
python scripts/compile_guide.py
```

**Output:**

- Parses all RST files with custom directives
- Generates SVG graphics and optimized images
- Creates `guide.json` with structured climbing data
- Embeds images as base64 or external references

**Key Features:**

- Custom HTML output writer with Climbers Heaven styling
- SVG topo generation for climbing routes
- Image optimization and AVIF conversion
- Geographic data integration from KML

### `images.py`

**Purpose:** Image collection, optimization, and embedding

**Usage:** Imported by `compile_guide.py`

**Functionality:**

- Collects images from route descriptions
- Optimizes and converts to AVIF format
- Embeds images or links external references
- Manages image metadata and captions

### `crags-scraper.py` & `eightanu_scraper.py`

**Purpose:** Scrape route information from external climbing databases

**Usage:**

```bash
python scripts/crags-scraper.py
python scripts/eightanu_scraper.py
```

**Purpose:** Import climbing route data from external sources to populate the guide.

## 🚢 Deployment

### Build for Production

```bash
# Compile content
cd scripts
python compile_guide.py
cd ../html

# Build frontend
npm run build

# Output is in ./build/
```

### PWA Deployment

The project builds as a Progressive Web App with:

- **Service Worker** (`sw.js`) — Enables offline access
- **Web App Manifest** (`manifest.webmanifest`) — Installation support
- **Prerendered Static Files** — All content is static HTML, CSS, and JavaScript

Deploy the `html/build/` directory to any static hosting service:

- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- Traditional web server (Apache, Nginx)

### Environment Variables

For production builds:

```bash
VITE_AS_PWA=1 npm run build
```

This enables PWA features for production deployment.

## 📝 Contributing

### Adding New Climbing Areas

1. **Create RST file** in appropriate region folder:

   ```bash
   touch docutil/podgorica/new-area/new-area.rst
   ```

2. **Add geolocation** with coordinates from Climbersheaven.kml
3. **Document routes** with grades, descriptions, and images
4. **Update main guide** (`docutil/guide.rst`) to link new area
5. **Recompile** with `python scripts/compile_guide.py`
6. **Test** locally with `npm run dev`

### Code Quality

Before submitting changes:

```bash
cd html
npm run lint              # Check formatting
npm run format            # Auto-fix formatting
npm run check             # Type-check components
npm test                  # Run tests
```

### Git Workflow

1. Create feature branch
2. Make changes and test locally
3. Commit with descriptive messages
4. Push and create pull request
5. Wait for CI/CD checks and review

## 🐛 Troubleshooting

### `compile_guide.py` fails with import errors

**Solution:** Verify all Python dependencies are installed:

```bash
conda list docutils Pillow svgelements
pip list | grep -E "drawsvg|pillow-avif-plugin|defusedxml|fastkml|levenshtein|minify-html"
```

Install missing packages as shown in Prerequisites.

### Dev server shows old content after editing RST

**Solution:** The dev server watches files but requires manual recompilation:

```bash
python scripts/compile_guide.py  # Recompile content
# Refresh browser
```

### Build size is too large

**Solution:** Check image optimization:

```bash
# Verify images are in AVIF format (smallest)
find docutil -name "*.png" -o -name "*.jpg"

# Use images.py to optimize remaining images
python scripts/images.py
```

### PWA not working offline

**Solution:** Verify service worker is generated:

```bash
# Check that build/ contains sw.js
ls -la html/build/sw.js

# Clear browser cache and reinstall PWA
```

## 📚 Additional Resources

- [docutil/readme.md](docutil/readme.md) — Custom RST directives documentation
- [html/README.md](html/README.md) — Frontend-specific setup and development
- [reStructuredText Documentation](https://docutils.sourceforge.io/rst.html)
- [Svelte Documentation](https://svelte.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Lingui i18n Documentation](https://lingui.dev)

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.

## 👥 Authors & Contributors

kochelmonster

---

**Last Updated:** 2026-07-08

For questions or issues, please refer to the troubleshooting section or open an issue in the project repository.
