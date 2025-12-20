/**
 * Utility functions for date formatting across the application
 */

/**
 * Safely format a date string, handling null/undefined values
 * Returns "N/A" for invalid or missing dates
 */
export const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) {
        return 'N/A';
    }

    try {
        const date = new Date(dateString);

        // Check if the date is valid
        if (isNaN(date.getTime())) {
            return 'N/A';
        }

        // Check if the date is suspiciously old (before year 2000)
        // This helps catch epoch-related bugs
        if (date.getFullYear() < 2000) {
            return 'N/A';
        }

        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    } catch {
        return 'N/A';
    }
};

/**
 * Format a date for display with time
 */
export const formatDateTime = (dateString: string | null | undefined): string => {
    if (!dateString) {
        return 'N/A';
    }

    try {
        const date = new Date(dateString);

        if (isNaN(date.getTime()) || date.getFullYear() < 2000) {
            return 'N/A';
        }

        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return 'N/A';
    }
};

/**
 * Get a safe timestamp for sorting, returns 0 for invalid dates
 */
export const getSafeTimestamp = (dateString: string | null | undefined): number => {
    if (!dateString) {
        return 0;
    }

    try {
        const date = new Date(dateString);
        const timestamp = date.getTime();

        // Return 0 for invalid dates or dates before year 2000
        if (isNaN(timestamp) || date.getFullYear() < 2000) {
            return 0;
        }

        return timestamp;
    } catch {
        return 0;
    }
};

/**
 * Check if a date is valid and after year 2000
 */
export const isValidDate = (dateString: string | null | undefined): boolean => {
    if (!dateString) {
        return false;
    }

    try {
        const date = new Date(dateString);
        return !isNaN(date.getTime()) && date.getFullYear() >= 2000;
    } catch {
        return false;
    }
};
