/**
 * CaptionFlow — Font System
 * Maps font families to Google Fonts + provides Devanagari fallbacks for Hindi.
 */

export interface FontOption {
  name: string;          // Display name
  family: string;        // CSS font-family value
  weights: string[];     // Available weights
  supportsDevanagari: boolean;
  googleFonts: boolean;
}

export const AVAILABLE_FONTS: FontOption[] = [
  {
    name: 'Poppins',
    family: 'Poppins',
    weights: ['400', '500', '600', '700', '800', '900'],
    supportsDevanagari: false,
    googleFonts: true,
  },
  {
    name: 'Inter',
    family: 'Inter',
    weights: ['400', '500', '600', '700', '800', '900'],
    supportsDevanagari: false,
    googleFonts: true,
  },
  {
    name: 'Montserrat',
    family: 'Montserrat',
    weights: ['400', '500', '600', '700', '800', '900'],
    supportsDevanagari: false,
    googleFonts: true,
  },
  {
    name: 'Noto Sans',
    family: 'Noto Sans',
    weights: ['400', '500', '600', '700', '800', '900'],
    supportsDevanagari: false,
    googleFonts: true,
  },
  {
    name: 'Noto Sans Devanagari',
    family: 'Noto Sans Devanagari',
    weights: ['400', '500', '600', '700', '800', '900'],
    supportsDevanagari: true,
    googleFonts: true,
  },
];

/**
 * Languages that use Devanagari script and need a compatible font.
 */
const DEVANAGARI_LANGUAGES = new Set(['hi', 'mr', 'ne', 'sa', 'mai', 'bho']);

/**
 * Get the best font family for a given language.
 * For Hindi and other Devanagari languages, always use Noto Sans Devanagari.
 */
export function getFontForLanguage(
  preferredFamily: string,
  language: string = 'en'
): string {
  if (DEVANAGARI_LANGUAGES.has(language)) {
    return 'Noto Sans Devanagari';
  }
  return preferredFamily;
}

/**
 * CSS font stack for a given font family with proper fallbacks.
 */
export function getFontStack(family: string): string {
  const fallbacks: Record<string, string> = {
    'Poppins': "'Poppins', 'Inter', 'Noto Sans', sans-serif",
    'Inter': "'Inter', 'Noto Sans', system-ui, sans-serif",
    'Montserrat': "'Montserrat', 'Inter', sans-serif",
    'Noto Sans': "'Noto Sans', system-ui, sans-serif",
    'Noto Sans Devanagari': "'Noto Sans Devanagari', 'Noto Sans', sans-serif",
  };
  return fallbacks[family] ?? `'${family}', 'Noto Sans', sans-serif`;
}

/**
 * Detect if text contains Devanagari Unicode characters.
 * Unicode range: U+0900–U+097F (Devanagari block)
 */
export function containsDevanagari(text: string): boolean {
  return /[\u0900-\u097F]/.test(text);
}

/**
 * Detect the best font for given text content.
 * Automatically selects Devanagari font if text contains Hindi.
 */
export function detectFontForText(text: string, preferredFamily: string): string {
  if (containsDevanagari(text)) {
    return 'Noto Sans Devanagari';
  }
  return preferredFamily;
}
