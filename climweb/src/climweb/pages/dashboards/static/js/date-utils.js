function formatDateTimeJS(datetimeString, formatStr) {
    const date = new Date(datetimeString);

    switch (formatStr) {
        case "yyyy-MM-dd HH:mm":
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
        case "yyyy-MM-dd":
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
        case "yyyy-MM":
            return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
        case "MMMM yyyy":
            return `${date.toLocaleString("default", { month: "long" })} ${date.getFullYear()}`;
        case "yyyy":
            return `${date.getFullYear()}`;
        case "pentadal":
            return pentadalLabel(date);
        case "dekadal":
            return dekadalLabel(date);
        default:
            return datetimeString;
    }
}


function pentadalLabel(date) {
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "short" });
    const year = date.getFullYear();
    let period = 1, range = "1-5th";
    if (day > 25) { period = 6; range = "26-end"; }
    else if (day > 20) { period = 5; range = "21-25th"; }
    else if (day > 15) { period = 4; range = "16-20th"; }
    else if (day > 10) { period = 3; range = "11-15th"; }
    else if (day > 5) { period = 2; range = "6-10th"; }
    return `${month} ${year} - P${period} ${range}`;
}

function dekadalLabel(date) {
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "short" });
    const year = date.getFullYear();
    let period = 1, range = "1-10th";
    if (day > 20) { period = 3; range = "21-end"; }
    else if (day > 10) { period = 2; range = "11-20th"; }
    return `${month} ${year} - D${period} ${range}`;
}


function formatDateTime(datetimeString) {
    const date = new Date(datetimeString);
    const day = date.getDate();
    const month = date.toLocaleString("default", { month: "long" });
    const year = date.getFullYear();
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${day} ${month} ${year} ${hours}:${minutes}`;
}


function initializeCalendar(id, onChange, defaultDates, dateFormat, availableDates = []) {
    const startInputEl = document.querySelector(`#date-start-${id}`);
    const endInputEl = document.querySelector(`#date-end-${id}`);
    let startTimeSelectEl = document.querySelector(`#time-start-${id}`);
    let endTimeSelectEl = document.querySelector(`#time-end-${id}`);


    if (!startInputEl || !endInputEl) {
        console.error(`Start or End date input not found for id: ${id}`);
        return;
    }

    // Map format to vanillajs-datepicker format
    let dpFormat = "yyyy-mm-dd";
    let displayFormat = "yyyy-MM-dd"; // Default display format
    let pickLevel = 0;
     switch (dateFormat) {
        case "yyyy":
            dpFormat = "yyyy";
            displayFormat = "yyyy";
            pickLevel = 2;
            break;
        case "yyyy-MM":
        case "MMMM yyyy":
            dpFormat = "yyyy-mm";
            displayFormat = "yyyy-MM";
            pickLevel = 1;
            break;
        case "yyyy-MM-dd":
            dpFormat = "yyyy-mm-dd";
            displayFormat = "yyyy-MM-dd";
            break;
        case "yyyy-MM-dd HH:mm":
            dpFormat = "yyyy-mm-dd"; // No time support in vanilla-datepicker
            displayFormat = "yyyy-MM-dd";
            break;
        default:
            dpFormat = "yyyy-mm-dd";
            displayFormat = "yyyy-MM-dd";
    }

    const availableDatesSet = new Set(
        availableDates.map((date) => {
          // Create a new Date object and reset the time to midnight (00:00:00)
          const dateWithoutTime = new Date(date);
          dateWithoutTime.setHours(0, 0, 0, 0);
          return formatDateTimeJS(dateWithoutTime, displayFormat);
        })
      );

      // Function to check if a date is available
      const isDateAvailable = (date) => {
        // Ensure the input date also has its time stripped
        const dateWithoutTime = new Date(date);
        dateWithoutTime.setHours(0, 0, 0, 0);
        const formattedDate = formatDateTimeJS(dateWithoutTime, displayFormat);


        return availableDatesSet.has(formattedDate);
      };

    // Initialize start and end datepickers
    const startDatepicker = new Datepicker(startInputEl, {
        format: dpFormat,
        autohide: true,
        todayHighlight: true,
        clearBtn: true,
        pickLevel,
        beforeShowDay: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowYear: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowMonth: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
    });

    const endDatepicker = new Datepicker(endInputEl, {
        format: dpFormat,
        autohide: true,
        todayHighlight: true,
        clearBtn: true,
        pickLevel,
        beforeShowDay: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowYear: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
        beforeShowMonth: (date) => {
            return isDateAvailable(date) ? { enabled: true } : { enabled: false };
        },
    });

    // Set default dates if provided
    if (defaultDates && defaultDates.length === 2) {
        startDatepicker.setDate(defaultDates[0]);
        endDatepicker.setDate(defaultDates[1]);
    }

    

    // Populate time selectors if time support is enabled
    if (dateFormat === "yyyy-MM-dd HH:mm") {
        const populateTimeSelector = (timeSelectEl, defaultTime) => {
            const times = [];
            for (let hour = 0; hour < 24; hour++) {
                for (let minute = 0; minute < 60; minute += 15) {
                    const time = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
                    times.push(time);
                }
            }
            timeSelectEl.innerHTML = times
                .map((time) => `<option value="${time}" ${time === defaultTime ? "selected" : ""}>${time}</option>`)
                .join("");
        };

        if (!startTimeSelectEl) {
            startTimeSelectEl = document.createElement("select");
            startTimeSelectEl.id = `time-start-${id}`;
            startTimeSelectEl.className = "timepicker-select input is-small";
            startInputEl.parentNode.insertBefore(startTimeSelectEl, startInputEl.nextSibling);
        }

        if (!endTimeSelectEl) {
            endTimeSelectEl = document.createElement("select");
            endTimeSelectEl.id = `time-end-${id}`;
            endTimeSelectEl.className = "timepicker-select input is-small";
            endInputEl.parentNode.insertBefore(endTimeSelectEl, endInputEl.nextSibling);
        }

        populateTimeSelector(startTimeSelectEl, "00:00");
        populateTimeSelector(endTimeSelectEl, "23:45");
    }

    // Format the displayed date to be human-friendly
    const formatDisplayDate = (date) => {
        if (!date) return "";
        return formatDateTimeJS(date, displayFormat); // Use formatDateTimeJS for human-friendly formatting
    };

    // Update the input fields with human-friendly dates
    const updateDisplayDates = () => {
        const startDate = startDatepicker.getDate();
        const endDate = endDatepicker.getDate();

        startInputEl.value = formatDisplayDate(startDate);
        endInputEl.value = formatDisplayDate(endDate);
    };

    // Handle date changes
    const handleDateChange = () => {
        const startDate = startDatepicker.getDate();
        const endDate = endDatepicker.getDate();
        const startTime = startTimeSelectEl ? startTimeSelectEl.value : "00:00";
        const endTime = endTimeSelectEl ? endTimeSelectEl.value : "00:00";

        if (startDate && endDate) {
            // Combine date and time into a single ISO string
            const [startHours, startMinutes] = startTime.split(":").map(Number);
            const [endHours, endMinutes] = endTime.split(":").map(Number);

            startDate.setHours(startHours || 0, startMinutes || 0, 0, 0);
            endDate.setHours(endHours || 0, endMinutes || 0, 0, 0);

            // Ensure start date is before or equal to end date
            if (startDate > endDate) {
                console.warn("Start date cannot be after end date");
                return;
            }

            // Trigger the onChange callback with the selected date range
            // onChange && onChange([startDate, endDate]);
            onChange([startDate, endDate]);
        }

        updateDisplayDates();

        
    };

    // Add event listeners for date changes
    startInputEl.addEventListener("changeDate", handleDateChange);
    endInputEl.addEventListener("changeDate", handleDateChange);

    if (startTimeSelectEl) startTimeSelectEl.addEventListener("change", handleDateChange);
    if (endTimeSelectEl) endTimeSelectEl.addEventListener("change", handleDateChange);

}

function getDateFormatFromContainer(container) {
    return container.dataset.datetimeFormat || "yyyy-MM-dd";
}





