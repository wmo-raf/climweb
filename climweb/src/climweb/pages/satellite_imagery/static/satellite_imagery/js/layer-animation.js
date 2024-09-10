function formatDate(dateString) {
    const daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

    const parsedTimestamp = Date.parse(dateString)
    const date = new Date(parsedTimestamp);

    // Get the day of the week and day of the month
    const dayOfWeek = daysOfWeek[date.getUTCDay()];
    const dayOfMonth = date.getUTCDate();

    // Get the time in HH:mm format
    const hours = String(date.getUTCHours()).padStart(2, '0');
    const minutes = String(date.getUTCMinutes()).padStart(2, '0');
    const time = `${hours}:${minutes}`;

    return `${dayOfWeek} ${dayOfMonth} - ${time}`;
}


function LayerAnimation(options) {
    const {layerDates, containerId, imagesArray} = options

    this.layerDates = layerDates
    this.container = $(`#${containerId}`)
    this.imagesArray = imagesArray
    this.plugin = undefined
    this.canvasEl = undefined
    this.$sliderEl = undefined

    this.init()
}

LayerAnimation.prototype.init = function () {
    this.initMarkup()
    this.initPlugin()
}

LayerAnimation.prototype.initMarkup = function () {

    this.container.empty()

    $(`<div class="animate-image-wrapper">
            <div class="animate-image-container">
                <canvas id="anim-image-canvas" class="anim-canvas"></canvas>
            </div>
            <div class="anim-controls">
                <div id="loading-indicator" class="anim-loading-indicator">Loading <span>0</span>%</div>
                <div id="anim-play-pause" class="anim-play-pause" style="display: none">
                    <div class="anim-icon">
                        <div class="icon-play">
                            <svg id="icon-play" viewbox="0 0 448 512">
                                <path d="M424.4 214.7L72.4 6.6C43.8-10.3 0 6.1 0 47.9V464c0 37.5 40.7 60.1 72.4 41.3l352-208c31.4-18.5 31.5-64.1 0-82.6z"/>
                            </svg>
                        </div>
                        <div class="icon-pause" style="display: none">
                            <svg id="icon-pause" viewbox="0 0 448 512">
                                <path d="M144 479H48c-26.5 0-48-21.5-48-48V79c0-26.5 21.5-48 48-48h96c26.5 0 48 21.5 48 48v352c0 26.5-21.5 48-48 48zm304-48V79c0-26.5-21.5-48-48-48h-96c-26.5 0-48 21.5-48 48v352c0 26.5 21.5 48 48 48h96c26.5 0 48-21.5 48-48z"/>
                            </svg>
                        </div>
                    </div>
                </div>
                <div class="anim-progress-line">
                    <div id="anim-slider" class="anim-slider"></div>
                </div>
            </div>
    </div>`).appendTo(this.container)

    this.canvasEl = document.getElementById("anim-image-canvas")
    this.$sliderEl = $("#anim-slider")
    this.loadingIndicator = $("#loading-indicator")
    this.$playPause = $("#anim-play-pause")
    this.$playIcon = $(".icon-play")
    this.$pauseIcon = $(".icon-pause")


    this.$playPause.click(() => {

        if (this.plugin) {

            if (this.plugin.isAnimating()) {
                this.plugin.stop()

                this.$pauseIcon.hide()
                this.$playIcon.show()
            } else {
                this.plugin.play()

                this.$playIcon.hide()
                this.$pauseIcon.show()
            }
        }

    })
}


LayerAnimation.prototype.initPlugin = function () {
    const that = this

    this.plugin = new AnimateImages(that.canvasEl, {
        images: that.imagesArray,
        preload: "partial",
        preloadNumber: 20,
        poster: that.imagesArray[0],
        fps: 10,
        loop: true,
        reverse: false,
        autoplay: false,
        fillMode: "contain",
        draggable: false,
        touchScrollMode: "allowPageScroll",
        onPosterLoaded(plugin) {
            plugin.preloadImages()
        },
        onPreloadFinished(plugin) {
            that.initControls()
        },
        onAfterFrame(plugin, {context, width, height}) {
            let currentFrame = plugin.getCurrentFrame()

            if (that.$sliderEl.slider && plugin.isAnimating()) {
                let valueIndex = currentFrame

                if (currentFrame === that.layerDates.length) {
                    valueIndex = 0
                }

                that.$sliderEl.slider("value", valueIndex)
                const dateValue = that.layerDates[valueIndex]
                const dateStr = formatDate(dateValue)

                that.$sliderEl.find(".ui-slider-tooltip-val").text(dateStr)
            }
        },
    })


    this.canvasEl.addEventListener("animate-images:loading-progress", function (e) {
        const percentage = Math.floor(+e.detail.progress * 100);
        that.loadingIndicator.find("span").text(percentage)
        if (percentage === 100) {
            that.loadingIndicator.hide()
        }
    });
}

LayerAnimation.prototype.initControls = function () {
    const minIndex = 0
    const maxIndex = this.layerDates.length - 1
    const initialIndex = 0

    const that = this

    this.$sliderEl.slider({
        range: "min",
        min: minIndex,
        max: maxIndex,
        value: initialIndex,
        slide: function (event, ui) {
            const dateValue = that.layerDates[ui.value]
            const dateStr = formatDate(dateValue)
            $(ui.handle).find('.ui-slider-tooltip-val').text(dateStr);

            const frame = ui.value + 1
            that.plugin.setFrame(frame)
        },
        create: function (event) {
            const tooltip = $('<div class="ui-slider-tooltip"><div class="ui-slider-tooltip-val"></div></div> ')
            const value = that.layerDates[initialIndex]
            const dateStr = formatDate(value)

            tooltip.find(".ui-slider-tooltip-val").text(dateStr)
            $(event.target).find('.ui-slider-handle').append(tooltip);

            const frame = initialIndex + 1
            that.plugin.setFrame(frame)

            that.$playPause.show()
        },
        change: function (event, ui) {
            if (that.plugin && !that.plugin.isAnimating()) {
                const frame = ui.value + 1
                that.plugin.setFrame(frame)
            }
        }
    });
}

LayerAnimation.prototype.destroy = function () {
    this.plugin.destroy()
    this.plugin = null

    if (this.$sliderEl.slider) {
        this.$sliderEl.slider("destroy")
    }

    this.container.empty()
}

