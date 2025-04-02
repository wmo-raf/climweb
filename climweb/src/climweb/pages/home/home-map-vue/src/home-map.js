import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {createI18n} from 'vue-i18n'
import DjangoUtilsPlugin, {convertDatasetToProps} from 'vue-plugin-django-utils'

import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import HomeMap from './components/home-map/HomeMap.vue'

const pinia = createPinia()

const i18n = createI18n({
    legacy: false,
    locale: 'en',
    fallbackLocale: 'en',
})

const homeMapEl = document.getElementById('home-map')

// If the element exists, mount the Vue app
if (homeMapEl) {
    const app = createApp(HomeMap, convertDatasetToProps({
        dataset: {...homeMapEl.dataset},
        component: HomeMap
    }))

    app.use(PrimeVue, {
        theme: {
            preset: Aura,
        }
    });

    app.use(pinia)
    app.use(i18n)
    app.use(DjangoUtilsPlugin, {rootElement: homeMapEl})
    app.mount(homeMapEl)
}