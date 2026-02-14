/**
 * Location Autocomplete Component
 * Provides country and city autocomplete functionality with continent grouping and flags.
 */

(function() {
    'use strict';

    console.log('Location autocomplete v3 loaded');

    // Convert country code to flag emoji
    function countryCodeToFlag(code) {
        if (!code || code.length !== 2) return '';
        const codePoints = code
            .toUpperCase()
            .split('')
            .map(char => 127397 + char.charCodeAt(0));
        return String.fromCodePoint(...codePoints);
    }

    // Debounce helper
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Country Autocomplete class (shows all countries grouped by continent)
    class CountryAutocomplete {
        constructor(inputId, hiddenInputId, options = {}) {
            this.input = document.getElementById(inputId);
            this.hiddenInput = document.getElementById(hiddenInputId);

            if (!this.input || !this.hiddenInput) {
                return;
            }

            this.options = {
                apiUrl: options.apiUrl || '/api/countries/search/',
                onSelect: options.onSelect || null,
                ...options
            };

            this.dropdown = null;
            this.allData = null;
            this.selectedIndex = -1;
            this.flatResults = [];
            this.isOpen = false;

            this.init();
        }

        init() {
            this.createDropdown();

            // Event listeners
            this.input.addEventListener('focus', () => this.onFocus());
            this.input.addEventListener('input', debounce(() => this.onInput(), 150));
            this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
            this.input.addEventListener('blur', () => this.onBlur());

            document.addEventListener('click', (e) => {
                if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
                    this.close();
                }
            });

            // ARIA
            this.input.setAttribute('role', 'combobox');
            this.input.setAttribute('aria-autocomplete', 'list');
            this.input.setAttribute('aria-expanded', 'false');
        }

        createDropdown() {
            this.dropdown = document.createElement('div');
            this.dropdown.className = 'country-dropdown';
            this.dropdown.setAttribute('role', 'listbox');
            this.dropdown.style.cssText = `
                position: absolute;
                z-index: 1000;
                width: max-content;
                min-width: 280px;
                max-width: 350px;
                max-height: 400px;
                overflow-y: auto;
                background: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 0.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
                display: none;
                margin-top: 4px;
                left: 0;
            `;

            const wrapper = this.input.parentElement;
            wrapper.style.position = 'relative';
            wrapper.appendChild(this.dropdown);
        }

        async onFocus() {
            if (!this.allData) {
                await this.loadAllCountries();
            }
            this.render(this.input.value.trim());
        }

        onInput() {
            if (this.allData) {
                this.render(this.input.value.trim());
            }
        }

        async loadAllCountries() {
            try {
                const response = await fetch(`${this.options.apiUrl}?all=1`);
                const data = await response.json();
                this.allData = data.continents || [];
            } catch (error) {
                console.error('Failed to load countries:', error);
                this.allData = [];
            }
        }

        render(filter = '') {
            this.dropdown.innerHTML = '';
            this.flatResults = [];
            this.selectedIndex = -1;

            const filterLower = filter.toLowerCase();

            this.allData.forEach(continent => {
                const filteredCountries = filter
                    ? continent.countries.filter(c =>
                        c.name.toLowerCase().includes(filterLower) ||
                        c.code.toLowerCase().includes(filterLower)
                    )
                    : continent.countries;

                if (filteredCountries.length === 0) return;

                // Continent header
                const header = document.createElement('div');
                header.className = 'continent-header';
                header.style.cssText = `
                    padding: 6px 12px;
                    font-size: 0.7rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: #d4af37;
                    background: #0a0a0a;
                    border-bottom: 1px solid #2d2d2d;
                    position: sticky;
                    top: 0;
                `;
                header.textContent = continent.name;
                this.dropdown.appendChild(header);

                // Countries
                filteredCountries.forEach(country => {
                    const item = this.createCountryItem(country);
                    this.dropdown.appendChild(item);
                    this.flatResults.push(country);
                });
            });

            if (this.flatResults.length === 0) {
                this.dropdown.innerHTML = `
                    <div style="padding: 12px; color: #808080; text-align: center;">
                        No countries found
                    </div>
                `;
            }

            this.open();
        }

        createCountryItem(country) {
            const div = document.createElement('div');
            div.className = 'country-item';
            div.setAttribute('role', 'option');
            div.setAttribute('data-id', country.id);
            div.setAttribute('data-name', country.name);
            div.setAttribute('data-code', country.code);

            const flag = countryCodeToFlag(country.code);
            const providerCount = country.provider_count || 0;

            div.innerHTML = `
                <span class="country-flag" style="margin-right: 8px; font-size: 1.1em;">${flag}</span>
                <span class="country-name" style="flex: 1;">${country.name}</span>
                <span class="provider-count" style="color: #808080; font-size: 0.8em; margin-left: 8px;">${providerCount > 0 ? providerCount : ''}</span>
            `;

            div.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                color: #f5f5f5;
                border-bottom: 1px solid #2d2d2d;
                display: flex;
                align-items: center;
                transition: background-color 0.15s;
            `;

            div.addEventListener('mouseenter', () => {
                div.style.backgroundColor = '#2d2d2d';
            });
            div.addEventListener('mouseleave', () => {
                div.style.backgroundColor = 'transparent';
            });
            div.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.select(country);
            });

            return div;
        }

        select(country) {
            this.input.value = country.name;
            this.hiddenInput.value = country.id;
            this.close();

            this.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));

            if (this.options.onSelect) {
                this.options.onSelect(country);
            }
        }

        open() {
            this.dropdown.style.display = 'block';
            this.isOpen = true;
            this.input.setAttribute('aria-expanded', 'true');
        }

        close() {
            this.dropdown.style.display = 'none';
            this.isOpen = false;
            this.selectedIndex = -1;
            this.input.setAttribute('aria-expanded', 'false');
        }

        onBlur() {
            setTimeout(() => {
                if (!this.dropdown.contains(document.activeElement)) {
                    this.close();
                }
            }, 200);
        }

        onKeyDown(e) {
            if (!this.isOpen) {
                if (e.key === 'ArrowDown' || e.key === 'Enter') {
                    e.preventDefault();
                    this.onFocus();
                }
                return;
            }

            const items = this.dropdown.querySelectorAll('.country-item');

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                    this.highlightItem(items);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                    this.highlightItem(items);
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (this.selectedIndex >= 0 && this.flatResults[this.selectedIndex]) {
                        this.select(this.flatResults[this.selectedIndex]);
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.close();
                    break;
            }
        }

        highlightItem(items) {
            items.forEach((item, idx) => {
                item.style.backgroundColor = idx === this.selectedIndex ? '#2d2d2d' : 'transparent';
                if (idx === this.selectedIndex) {
                    item.scrollIntoView({ block: 'nearest' });
                }
            });
        }

        clear() {
            this.input.value = '';
            this.hiddenInput.value = '';
            this.close();
        }

        setValue(id, name) {
            this.hiddenInput.value = id;
            this.input.value = name;
        }
    }

    // City Autocomplete class (shows all cities for selected country)
    class CityAutocomplete {
        constructor(inputId, hiddenInputId, options = {}) {
            this.input = document.getElementById(inputId);
            this.hiddenInput = document.getElementById(hiddenInputId);

            if (!this.input || !this.hiddenInput) {
                return;
            }

            this.options = {
                apiUrl: options.apiUrl || '/api/cities/search/',
                countryInputId: options.countryInputId || 'country_id',
                onSelect: options.onSelect || null,
                ...options
            };

            this.dropdown = null;
            this.allCities = [];
            this.filteredResults = [];
            this.selectedIndex = -1;
            this.isOpen = false;
            this.currentCountryId = null;

            this.init();
        }

        init() {
            this.createDropdown();

            this.input.addEventListener('focus', () => this.onFocus());
            this.input.addEventListener('input', debounce(() => this.onInput(), 150));
            this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
            this.input.addEventListener('blur', () => this.onBlur());

            document.addEventListener('click', (e) => {
                if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
                    this.close();
                }
            });

            this.input.setAttribute('role', 'combobox');
            this.input.setAttribute('aria-autocomplete', 'list');
            this.input.setAttribute('aria-expanded', 'false');
        }

        createDropdown() {
            this.dropdown = document.createElement('div');
            this.dropdown.className = 'city-dropdown';
            this.dropdown.setAttribute('role', 'listbox');
            this.dropdown.style.cssText = `
                position: absolute;
                z-index: 1000;
                width: max-content;
                min-width: 220px;
                max-width: 300px;
                max-height: 350px;
                overflow-y: auto;
                background: #1a1a1a;
                border: 1px solid #3d3d3d;
                border-radius: 0.5rem;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
                display: none;
                margin-top: 4px;
                left: 0;
            `;

            const wrapper = this.input.parentElement;
            wrapper.style.position = 'relative';
            wrapper.appendChild(this.dropdown);
        }

        async onFocus() {
            const countryInput = document.getElementById(this.options.countryInputId);
            const countryId = countryInput ? countryInput.value : '';

            if (!countryId) {
                this.showMessage('Select a country first');
                return;
            }

            // Reload cities if country changed
            if (countryId !== this.currentCountryId) {
                this.currentCountryId = countryId;
                this.allCities = [];
                await this.loadAllCities(countryId);
            }

            this.render(this.input.value.trim());
        }

        onInput() {
            if (this.allCities.length > 0) {
                this.render(this.input.value.trim());
            }
        }

        async loadAllCities(countryId) {
            try {
                const response = await fetch(`${this.options.apiUrl}?country=${countryId}&all=1`);
                const data = await response.json();
                this.allCities = data.results || [];
            } catch (error) {
                console.error('Failed to load cities:', error);
                this.allCities = [];
            }
        }

        render(filter = '') {
            this.dropdown.innerHTML = '';
            this.selectedIndex = -1;

            const filterLower = filter.toLowerCase();
            this.filteredResults = filter
                ? this.allCities.filter(c => c.name.toLowerCase().includes(filterLower))
                : this.allCities;

            if (this.filteredResults.length === 0) {
                this.showMessage('No cities found');
                return;
            }

            this.filteredResults.forEach(city => {
                const div = document.createElement('div');
                div.className = 'city-item';
                div.setAttribute('role', 'option');
                div.setAttribute('data-id', city.id);

                const providerCount = city.provider_count || 0;

                div.innerHTML = `
                    <span style="flex: 1;">${city.name}${city.is_capital ? ' ★' : ''}</span>
                    <span style="color: #808080; font-size: 0.8em; margin-left: 8px;">${providerCount > 0 ? providerCount : ''}</span>
                `;

                div.style.cssText = `
                    padding: 8px 12px;
                    cursor: pointer;
                    color: #f5f5f5;
                    border-bottom: 1px solid #2d2d2d;
                    display: flex;
                    align-items: center;
                    transition: background-color 0.15s;
                `;

                div.addEventListener('mouseenter', () => div.style.backgroundColor = '#2d2d2d');
                div.addEventListener('mouseleave', () => div.style.backgroundColor = 'transparent');
                div.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    this.select(city);
                });

                this.dropdown.appendChild(div);
            });

            this.open();
        }

        showMessage(msg) {
            this.dropdown.innerHTML = `<div style="padding: 12px; color: #808080; text-align: center;">${msg}</div>`;
            this.open();
        }

        select(city) {
            this.input.value = city.name;
            this.hiddenInput.value = city.id;
            this.close();

            this.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));

            if (this.options.onSelect) {
                this.options.onSelect(city);
            }
        }

        open() {
            this.dropdown.style.display = 'block';
            this.isOpen = true;
            this.input.setAttribute('aria-expanded', 'true');
        }

        close() {
            this.dropdown.style.display = 'none';
            this.isOpen = false;
            this.selectedIndex = -1;
            this.input.setAttribute('aria-expanded', 'false');
        }

        onBlur() {
            setTimeout(() => {
                if (!this.dropdown.contains(document.activeElement)) {
                    this.close();
                }
            }, 200);
        }

        onKeyDown(e) {
            if (!this.isOpen) {
                if (e.key === 'ArrowDown' || e.key === 'Enter') {
                    e.preventDefault();
                    this.onFocus();
                }
                return;
            }

            const items = this.dropdown.querySelectorAll('.city-item');

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
                    this.highlightItem(items);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                    this.highlightItem(items);
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (this.selectedIndex >= 0 && this.filteredResults[this.selectedIndex]) {
                        this.select(this.filteredResults[this.selectedIndex]);
                    }
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.close();
                    break;
            }
        }

        highlightItem(items) {
            items.forEach((item, idx) => {
                item.style.backgroundColor = idx === this.selectedIndex ? '#2d2d2d' : 'transparent';
                if (idx === this.selectedIndex) {
                    item.scrollIntoView({ block: 'nearest' });
                }
            });
        }

        clear() {
            this.input.value = '';
            this.hiddenInput.value = '';
            this.allCities = [];
            this.currentCountryId = null;
            this.close();
        }

        setValue(id, name) {
            this.hiddenInput.value = id;
            this.input.value = name;
        }

        disable() {
            this.input.disabled = true;
            this.input.style.opacity = '0.5';
        }

        enable() {
            this.input.disabled = false;
            this.input.style.opacity = '1';
        }
    }

    // Initialize
    function initLocationAutocomplete() {
        // Desktop country autocomplete
        if (document.getElementById('country-autocomplete')) {
            window.countryAutocomplete = new CountryAutocomplete('country-autocomplete', 'country_id', {
                onSelect: function() {
                    if (window.cityAutocomplete) {
                        window.cityAutocomplete.enable();
                        window.cityAutocomplete.clear();
                    }
                }
            });
        }

        // Desktop city autocomplete
        if (document.getElementById('city-autocomplete')) {
            window.cityAutocomplete = new CityAutocomplete('city-autocomplete', 'city_id', {
                countryInputId: 'country_id'
            });

            const countryId = document.getElementById('country_id');
            if (!countryId || !countryId.value) {
                window.cityAutocomplete.disable();
            }
        }

        // Mobile country autocomplete
        if (document.getElementById('country-autocomplete-mobile')) {
            window.countryAutocompleteMobile = new CountryAutocomplete('country-autocomplete-mobile', 'country_id_mobile', {
                onSelect: function() {
                    if (window.cityAutocompleteMobile) {
                        window.cityAutocompleteMobile.enable();
                        window.cityAutocompleteMobile.clear();
                    }
                }
            });
        }

        // Mobile city autocomplete
        if (document.getElementById('city-autocomplete-mobile')) {
            window.cityAutocompleteMobile = new CityAutocomplete('city-autocomplete-mobile', 'city_id_mobile', {
                countryInputId: 'country_id_mobile'
            });
        }

        // Clear button
        const clearBtn = document.getElementById('clear-filters');
        if (clearBtn) {
            clearBtn.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = window.location.pathname;
            });
        }
    }

    window.CountryAutocomplete = CountryAutocomplete;
    window.CityAutocomplete = CityAutocomplete;
    window.initLocationAutocomplete = initLocationAutocomplete;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLocationAutocomplete);
    } else {
        initLocationAutocomplete();
    }
})();
