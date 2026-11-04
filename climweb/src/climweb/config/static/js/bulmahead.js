const debounce = (callback, wait) => {
    let timeoutId = null;
    return (...args) => {
        window.clearTimeout(timeoutId);
        timeoutId = window.setTimeout(() => {
            callback.apply(null, args);
        }, wait);
    };
}

/**
 * Autocomplete for a Bulma dropdown, following the ARIA combobox pattern:
 * the input keeps focus, ↑/↓ move through the suggestions, Enter picks one,
 * Esc closes the list, and the number of results is announced.
 */
const bulmaHead = (id, idMenu, api, onSelect, delay, minLen = 2) => {
    const input = document.getElementById(id)
    const menuEl = document.getElementById(idMenu)
    menuEl.innerHTML = '<div class="dropdown-content"></div>'

    let options = []
    let activeIndex = -1

    input.setAttribute('role', 'combobox')
    input.setAttribute('aria-autocomplete', 'list')
    input.setAttribute('aria-controls', idMenu)
    input.setAttribute('aria-expanded', 'false')
    input.removeAttribute('aria-haspopup')
    if (!input.labels?.length && !input.hasAttribute('aria-label') && input.placeholder) {
        input.setAttribute('aria-label', input.placeholder)
    }
    menuEl.setAttribute('role', 'listbox')

    const announceResults = text => {
        if (typeof announce === 'function') announce(text)
    }

    const setOpen = open => {
        menuEl.style.display = open ? 'block' : 'none'
        input.setAttribute('aria-expanded', open ? 'true' : 'false')
        if (!open) setActive(-1)
    }

    const setActive = index => {
        options.forEach((opt, i) => {
            const active = i === index
            opt.classList.toggle('is-active', active)
            opt.setAttribute('aria-selected', active ? 'true' : 'false')
        })
        activeIndex = index
        if (index >= 0 && options[index]) {
            input.setAttribute('aria-activedescendant', options[index].id)
            options[index].scrollIntoView({block: 'nearest'})
        } else {
            input.removeAttribute('aria-activedescendant')
        }
    }

    const select = option => {
        const label = option.textContent
        const value = option.dataset.value
        input.value = label
        setOpen(false)
        if (onSelect) {
            onSelect({label, value})
        }
    }

    const setValue = e => {
        e.preventDefault()
        select(e.currentTarget)
        return false
    }

    const handleApi = e => {
        const value = e.target.value
        setOpen(false)
        options = []
        menuEl.innerHTML = '<div class="dropdown-content"></div>'
        if (value.length <= minLen) {
            return
        }

        api(value).then(suggestions => {
            options = suggestions.map(({label, value}, i) => {
                const a = document.createElement('a')
                a.href = '#'
                a.id = `${idMenu}-option-${i}`
                a.classList.add('dropdown-item')
                a.setAttribute('role', 'option')
                a.setAttribute('aria-selected', 'false')
                a.tabIndex = -1
                a.textContent = label
                a.dataset.value = value
                a.addEventListener('click', setValue)
                return a
            })

            options.forEach(optEl => {
                menuEl.childNodes[0].appendChild(optEl)
            })

            if (suggestions.length === 0) {
                const div = document.createElement('div')
                div.classList.add('dropdown-item')
                div.textContent = 'No result'
                menuEl.childNodes[0].appendChild(div)
                announceResults('No result')
            } else {
                announceResults(`${suggestions.length} result${suggestions.length === 1 ? '' : 's'} available. Use up and down arrows to choose.`)
            }

            setOpen(true)
        })
    }
    input.addEventListener('input', debounce(handleApi, delay))

    input.addEventListener('keydown', e => {
        const open = input.getAttribute('aria-expanded') === 'true'
        if (e.key === 'ArrowDown' && options.length) {
            e.preventDefault()
            if (!open) setOpen(true)
            setActive(activeIndex < options.length - 1 ? activeIndex + 1 : 0)
        } else if (e.key === 'ArrowUp' && options.length) {
            e.preventDefault()
            if (!open) setOpen(true)
            setActive(activeIndex > 0 ? activeIndex - 1 : options.length - 1)
        } else if (e.key === 'Enter' && open && activeIndex >= 0) {
            e.preventDefault()
            select(options[activeIndex])
        } else if (e.key === 'Escape' && open) {
            e.preventDefault()
            setOpen(false)
        }
    })

    input.addEventListener('focusout', e => {
        if (e.relatedTarget === null || !e.relatedTarget.classList.contains('dropdown-item')) {
            setOpen(false)
        }
    })

    input.addEventListener('focusin', handleApi)
}

window.bulmaHead = bulmaHead
