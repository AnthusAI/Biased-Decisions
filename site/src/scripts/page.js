// Runs on every page (the site's `chrome.scripts`): the page is static HTML built from the data contract.
import { watchFragment } from "./hash.js";

watchFragment();
