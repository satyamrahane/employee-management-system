/**
 * Date formatting utilities for Employee Management System.
 * Ensures consistent DD-MM-YYYY presentation without timezone shifts.
 */

/**
 * Formats a date string (expected in YYYY-MM-DD or ISO format) to DD-MM-YYYY.
 * Example: "2023-03-15" -> "15-03-2023"
 * Example: "2026-10-10" -> "10-10-2026"
 */
export function formatDateDDMMYYYY(dateStr?: string | null): string {
  if (!dateStr || typeof dateStr !== 'string') return '';
  
  // Extract date-only part if ISO timestamp format is passed
  const cleanStr = dateStr.includes('T') ? dateStr.split('T')[0] : dateStr.trim();
  const parts = cleanStr.split('-');
  
  if (parts.length === 3 && parts[0].length === 4) {
    const year = parts[0];
    const month = parts[1].padStart(2, '0');
    const day = parts[2].padStart(2, '0');
    return `${day}-${month}-${year}`;
  }
  
  return cleanStr;
}

/**
 * Converts a DD-MM-YYYY string to standard YYYY-MM-DD format for backend persistence.
 * Example: "15-03-2023" -> "2023-03-15"
 */
export function parseDDMMYYYYToISO(displayDate?: string | null): string {
  if (!displayDate || typeof displayDate !== 'string') return '';
  
  const parts = displayDate.trim().split('-');
  if (parts.length === 3 && parts[2].length === 4) {
    const day = parts[0].padStart(2, '0');
    const month = parts[1].padStart(2, '0');
    const year = parts[2];
    return `${year}-${month}-${day}`;
  }
  
  return displayDate.trim();
}
