/** @type {import("eslint").Linter.Config} */

module.exports = {
  // Prevent cascading in contained folders
  // root: true,

  /**
   * Reference:
   *
   * https://github.com/JulianCataldo/web-garden/blob/develop/configs/eslint-all.cjs
   *
   * */
  extends: [
    './node_modules/webdev-configs/eslint-all.cjs',

    // Or cherry pick one or more LANG: astro | js | jsx | ts | tsx | vue | mdx
    // './node_modules/webdev-configs/eslint-{LANG}.cjs',
  ],
};
