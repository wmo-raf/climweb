window.onscroll = function () { myFunction() };

var navbar = document.getElementById("sticky_nav");
var sticky = navbar.offsetTop;

function myFunction() {
    if (window.pageYOffset >= sticky) {
        navbar.classList.add("sticky")
    } else {
        navbar.classList.remove("sticky");
    }
}
$('ul li').each(function (i) {
    var t = $(this);

    t.css({
        'animation': 'slideInUp',
        'animation-duration': `${i * 0.4}s`
    })
    // setTimeout(function () { t.addClass('animation'); }, (i + 1) * 50);
});
let tabsWithContent = (function () {
    let tabs = document.querySelectorAll('.tabs li');
    let tabsContent = document.querySelectorAll('.tab-content');

    let deactvateAllTabs = function () {
        tabs.forEach(function (tab) {
            tab.classList.remove('is-active');
        });
    };

    let hideTabsContent = function () {
        tabsContent.forEach(function (tabContent) {
            tabContent.classList.remove('is-active');
        });
    };

    let activateTabsContent = function (tab) {
        tabsContent[getIndex(tab)].classList.add('is-active');
    };

    let getIndex = function (el) {
        return [...el.parentElement.children].indexOf(el);
    };

    tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
            deactvateAllTabs();
            hideTabsContent();
            tab.classList.add('is-active');
            activateTabsContent(tab);
        });
    })

    tabs[0].click();
})();

mapboxgl.accessToken = 'pk.eyJ1IjoiZ3JhY2VhbW9uZGkiLCJhIjoiY2s4dGphcGQwMDBhcjNmcnkzdGk3MnlrZCJ9.54r40Umo0l3dHseEbrQpUg';
const homeMap = new mapboxgl.Map({
    container: 'home-map', // container ID
    // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
    style: 'mapbox://styles/mapbox/light-v10', // style URL
    center: [30.61964793664734,
        12.859737131856392], // starting position [lng, lat]
    zoom: 4,// starting zoom,
    scrollZoom: false

});

const climateMap = new mapboxgl.Map({
    container: 'climate-map', // container ID
    // Choose from Mapbox's core styles, or make your own style with Mapbox Studio
    style: 'mapbox://styles/mapbox/dark-v10', // style URL
    center: [30.61964793664734,
        12.859737131856392], // starting position [lng, lat]
    zoom: 4, // starting zoom
    scrollZoom: false

});