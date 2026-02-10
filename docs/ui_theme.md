# UI Theme Documentation

This document describes the dark/sophisticated theme system implemented for the Massage Marketplace platform.

## Color Palette

### Primary Dark Colors
| Name | Hex Code | Usage |
|------|----------|-------|
| Dark (default) | `#0a0a0a` | Main background |
| Dark 50 | `#1a1a1a` | Navigation, footer, cards |
| Dark 100 | `#242424` | Card backgrounds |
| Dark 200 | `#2d2d2d` | Hover states, secondary backgrounds |
| Dark 300 | `#3d3d3d` | Borders |
| Dark 400 | `#4d4d4d` | Disabled states |

### Accent Colors (Red)
| Name | Hex Code | Usage |
|------|----------|-------|
| Accent (default) | `#8b1538` | CTA buttons, primary actions |
| Accent Light | `#a31d47` | Hover states |
| Accent Dark | `#6b1030` | Active/pressed states |

### Gold Colors
| Name | Hex Code | Usage |
|------|----------|-------|
| Gold (default) | `#d4af37` | Branding, highlights, links |
| Gold Light | `#e6c757` | Hover states |
| Gold Dark | `#b8952f` | Active/pressed states |

### Text Colors
| Name | Hex Code | Usage |
|------|----------|-------|
| Primary | `#f5f5f5` | Headings, important text |
| Secondary | `#b8b8b8` | Body text, descriptions |
| Muted | `#808080` | Placeholders, hints |

### Additional Colors
| Name | Hex Code | Usage |
|------|----------|-------|
| Deep Purple | `#4a1a4a` | Hero gradients, special accents |

## Typography

### Fonts
The theme uses two Google Fonts:

1. **Inter** (sans-serif) - Primary UI font
   - Weights: 300, 400, 500, 600, 700
   - Usage: All body text, buttons, navigation

2. **Playfair Display** (serif) - Display font
   - Weights: 400, 600, 700
   - Usage: Headings, logo, decorative text

### Font Loading
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet">
```

### Tailwind Configuration
```javascript
fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    display: ['Playfair Display', 'Georgia', 'serif'],
}
```

## Component Specifications

### Buttons

#### Gold Button (.btn-gold)
```css
background: linear-gradient(135deg, #d4af37, #b8952f);
color: #0a0a0a;
font-weight: 600;
padding: 10px 24px;
border-radius: 6px;
```

#### Accent Button (.btn-accent)
```css
background: linear-gradient(135deg, #8b1538, #a31d47);
color: #f5f5f5;
font-weight: 600;
padding: 10px 24px;
border-radius: 6px;
```

### Cards (.card-dark)
```css
background-color: #242424;
border: 1px solid #3d3d3d;
border-radius: 12px;
```
On hover:
- Border color changes to gold (#d4af37)
- Box shadow added

### Form Inputs (.input-dark)
```css
background-color: #1a1a1a;
border: 1px solid #3d3d3d;
color: #f5f5f5;
border-radius: 6px;
padding: 10px 14px;
```
On focus:
- Border color: #d4af37
- Box shadow: 0 0 0 3px rgba(212, 175, 55, 0.15)

### Select Dropdowns (.select-dark)
Same as input-dark with custom dropdown arrow styling.

## Location System Architecture

### Database Models

#### Continent
- `name` - Display name (e.g., "Europe")
- `code` - 2-character code (e.g., "EU")
- `display_order` - Sorting order

#### Country
- `name` - Full country name
- `code` - ISO 3166-1 alpha-2 code
- `continent` - ForeignKey to Continent
- `is_active` - Whether available for selection
- **Note**: United States is excluded from the database

#### City
- `name` - City name
- `country` - ForeignKey to Country
- `population` - For sorting
- `is_capital` - Boolean flag
- `is_major_city` - Boolean (population > 500k)
- `latitude/longitude` - Coordinates

### Provider Location Fields
- `country` - ForeignKey to Country (nullable)
- `city` - ForeignKey to City (nullable)

## Autocomplete API Endpoints

### Country Search
```
GET /api/countries/search/?q={query}
```
**Parameters:**
- `q` (required): Search query (min 2 characters)

**Response:**
```json
{
  "results": [
    {
      "id": 3,
      "name": "United Kingdom",
      "code": "GB",
      "continent": "Europe",
      "continent_code": "EU"
    }
  ]
}
```

### City Search
```
GET /api/cities/search/?q={query}&country={country_id}
```
**Parameters:**
- `q` (required): Search query (min 2 characters)
- `country` (required): Country ID

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "London",
      "country": "United Kingdom",
      "is_capital": true,
      "is_major_city": true
    }
  ]
}
```

## JavaScript Autocomplete Component

### Initialization
```javascript
// Auto-initializes on DOM ready
// Or manually:
initLocationAutocomplete();
```

### HTML Structure Required
```html
<!-- Country -->
<input type="text" id="country-autocomplete" placeholder="Search country...">
<input type="hidden" name="country_id" id="country_id">

<!-- City -->
<input type="text" id="city-autocomplete" placeholder="Search city...">
<input type="hidden" name="city_id" id="city_id">
```

### Features
- Debounced search (300ms)
- Keyboard navigation (Arrow Up/Down, Enter, Escape)
- Continent grouping in country results
- City selector disabled until country selected
- Touch-friendly dropdowns
- ARIA attributes for accessibility

### Public Methods
```javascript
window.countryAutocomplete.clear();      // Clear selection
window.countryAutocomplete.setValue(id, name);  // Set programmatically
window.cityAutocomplete.disable();       // Disable input
window.cityAutocomplete.enable();        // Enable input
```

## Accessibility Features

### Color Contrast
All text colors meet WCAG AA contrast requirements (4.5:1 minimum).

### Focus States
- Gold outline (2px solid #d4af37)
- Offset of 2px for visibility

### ARIA Attributes
- `role="combobox"` on autocomplete inputs
- `aria-autocomplete="list"`
- `aria-expanded` for dropdown state
- `role="listbox"` on dropdown containers
- `role="option"` on dropdown items

### Keyboard Navigation
- Tab: Move between form fields
- Arrow keys: Navigate dropdown options
- Enter: Select highlighted option
- Escape: Close dropdown

## Browser Support

| Browser | Minimum Version |
|---------|----------------|
| Chrome | 88+ |
| Firefox | 85+ |
| Safari | 14+ |
| Edge | 88+ |
| Mobile Chrome | 88+ |
| Mobile Safari | 14+ |

## Performance Optimization

### Debouncing
- Autocomplete searches debounced at 300ms
- Prevents excessive API calls

### Indexes
Database indexes on:
- Country: continent + name, is_active
- City: country + name, is_major_city

### Result Limits
- Maximum 20 results returned per API call
- Cities ordered by is_capital, is_major_city, population

### Lazy Loading
- Tailwind CSS loaded via CDN
- Google Fonts with `display=swap`

## Fixture Data

### Loading Fixtures
```bash
cd marketplace
python manage.py loaddata 001_continents.json
python manage.py loaddata 002_countries.json
python manage.py loaddata 003_cities_europe.json
python manage.py loaddata 004_cities_asia.json
python manage.py loaddata 005_cities_africa.json
python manage.py loaddata 006_cities_south_america.json
python manage.py loaddata 007_cities_oceania.json
```

### Data Sources
- Continents: Standard 6-continent model
- Countries: ISO 3166-1 (excluding US)
- Cities: Capitals + cities with population > 500k

### Updating Fixtures
1. Edit JSON files in `providers/fixtures/`
2. Re-run loaddata commands
3. Note: Existing data will be updated by PK

## File Locations

| File | Purpose |
|------|---------|
| `templates/base.html` | Global dark theme, Tailwind config |
| `templates/clients/provider_list.html` | Provider directory with filters |
| `templates/clients/provider_detail.html` | Provider profile page |
| `static/js/location-autocomplete.js` | Autocomplete component |
| `providers/models.py` | Continent, Country, City models |
| `clients/views.py` | Search API endpoints |
| `providers/fixtures/*.json` | Location data |
