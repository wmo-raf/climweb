import {endOfMonth, format as dateFormat, parseISO} from "date-fns";

export const defined = (value) => {
    return value !== undefined && value !== null;
};

export const getNextToNowDate = (dates) => {
    // Get the current date time
    const now = new Date();

    // Find the date that is one step ahead of the current date time,assuming the dates are ordered
    const nextDate = dates.find((dateStr) => {
        const date = new Date(dateStr);
        return date > now;
    });

    // Return the next date, or null if there isn't one
    return nextDate || null;
};


export const getPreviousToNowDate = (dates) => {
    // Get the current date time
    const now = new Date();

    // Find the date that is one step behind the current date time, assuming the dates are ordered
    const previousDate = dates.reverse().find((dateStr) => {
        const date = new Date(dateStr);
        return date < now;
    });

    // Return the previous date, or null if there isn't one
    return previousDate || null;
};

export const getTimeFromList = (timestamps, currentTimeMethod) => {
    let currentTime = timestamps[timestamps.length - 1];

    switch (currentTimeMethod) {
        case "next_to_now":
            const nextDate = getNextToNowDate(timestamps);
            if (nextDate) {
                currentTime = nextDate;
            }
            break;
        case "previous_to_now":
            const previousDate = getPreviousToNowDate(timestamps);
            if (previousDate) {
                currentTime = previousDate;
            }
            break;
        case "latest_from_source":
            currentTime = timestamps[timestamps.length - 1];
            break;
        case "earliest_from_source":
            currentTime = timestamps[0];
            break;
        default:
            break;
    }

    return currentTime;
};

/**
 * Formats a date according to the locale if provided, otherwise in a dd/mm/yyyy format.
 *
 * @param {Date} d the date to format
 * @param {Locale} [locale] the locale to use for formatting
 * @returns {string} A formatted date.
 */
export function formatDate(d, locale) {
    if (defined(locale)) {
        return d.toLocaleDateString(locale);
    }
    return [pad(d.getDate()), pad(d.getMonth() + 1), d.getFullYear()].join("/");
}

/**
 * Formats the time according to the locale if provided, otherwise in a hh:mm:ss format.
 *
 * @param {Date} d the date to format
 * @param {Locale} [locale] the locale to use for formatting
 * @returns {string} A formatted time.
 */
export function formatTime(d, locale) {
    if (defined(locale)) {
        return d.toLocaleTimeString(locale);
    }
    return [pad(d.getHours()), pad(d.getMinutes()), pad(d.getSeconds())].join(
        ":"
    );
}

/**
 * Combines {@link #formatDate} and {@link #formatTime}.
 *
 * @param {Date} d the date to format
 * @param {Locale} [locale] the locale to use for formatting
 * @returns {string} A formatted date and time with a comma separating them.
 */
export function formatDateTime(d, locale) {
    return formatDate(d, locale) + ", " + formatTime(d, locale);
}

/**
 * Puts a leading 0 in front of a number of it's less than 10.
 *
 * @param {number} s A number to pad
 * @returns {string} A string representing a two-digit number.
 */
function pad(s) {
    return s < 10 ? "0" + s : `${s}`;
}

const getOrdinalNum = (number) => {
    let selector;

    if (number <= 0) {
        selector = 4;
    } else if ((number > 3 && number < 21) || number % 10 > 3) {
        selector = 0;
    } else {
        selector = number % 10;
    }

    return number + ["th", "st", "nd", "rd", ""][selector];
};

export function getPentadFromDateString(date) {
    let dateObj;

    if (typeof date === "string") {
        dateObj = parseISO(date);
    } else {
        dateObj = date;
    }

    const lastDayOfMonth = endOfMonth(dateObj).getDate();

    const day = dateObj.getDate();

    if (day <= 5) {
        return [1, "1-5th", 1];
    }

    if (day <= 10) {
        return [2, "6-10th", 6];
    }

    if (day <= 15) {
        return [3, "11-15th", 11];
    }

    if (day <= 20) {
        return [4, "16-20th", 16];
    }

    if (day <= 25) {
        return [4, "21-25th", 21];
    }
    return [6, `26-${getOrdinalNum(lastDayOfMonth)}`, 26];
}

export function getDekadFromString(date) {
    let dateObj;

    if (typeof date === "string") {
        dateObj = parseISO(date);
    } else {
        dateObj = date;
    }

    const lastDayOfMonth = endOfMonth(dateObj).getDate();

    const day = dateObj.getDate();

    if (day <= 10) {
        return [1, "1-10th", 1];
    }

    if (day <= 20) {
        return [2, "11-20th", 11];
    }

    return [3, `21-${getOrdinalNum(lastDayOfMonth)}`, 21];
}

export function dFormatter(date, format, asPeriod) {
    let dateObj;

    if (typeof date === "string") {
        dateObj = parseISO(date);
    } else {
        dateObj = date;
    }

    let formated = dateFormat(dateObj, format);

    if (asPeriod) {
        if (asPeriod === "pentadal") {
            const [pentad, duration] = getPentadFromDateString(date);

            formated = `${formated} - P${pentad} ${duration}`;
        } else if (asPeriod === "dekadal") {
            const [dekad, duration] = getDekadFromString(date);

            formated = `${formated} - D${dekad} ${duration}`;
        }
    }

    return formated;
}

export function sortDates(datesList) {
    return datesList.sort((a, b) => {
        const dateA = new Date(a);
        const dateB = new Date(b);

        return dateA - dateB;
    });
}