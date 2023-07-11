// ==UserScript==
// @name         Test
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  try to take over the world!
// @author       You
// @match        *://anime.jhiday.net/hof/user/ImagineBrkr*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=google.com
// @grant        none
// @updateURL    https://raw.githubusercontent.com/ImagineBrkr/mal_awc_tamper_scripts/main/hide_completed_challenges.js
// @downloadURL  https://raw.githubusercontent.com/ImagineBrkr/mal_awc_tamper_scripts/main/hide_completed_challenges.js
// @run-at       document-end
// ==/UserScript==
let url = 'https://raw.githubusercontent.com/ImagineBrkr/mal_awc_tamper_scripts/main/challengeList.json';

function hide_challenges(completed_challenges) {
    var count = 0;
    var interval = setInterval(function () {
        var divElements = Array.from(document.querySelectorAll('div'));
        var matchingDivs = divElements.filter(div => /^content-category-\d+$/.test(div.id));

        matchingDivs.forEach(function (divElement) {
            var aElements = divElement.getElementsByTagName('a');

            for (var i = 0; i < aElements.length; i++) {
                count += 1;
                if (completed_challenges.includes(aElements[i].textContent)) {
                    aElements[i].parentNode.remove();
                    console.log('Removed ' + aElements[i].textContent + ' challenge')
                }
            }
        });
        if (count > 3000) {
            clearInterval(interval); // stop the interval once the elements are found and removed
            console.log('Interval cleared.'); // log interval cleared
        }
    }, 1000); // repeat every 1000ms (1 second)
}

fetch(url)
    .then(response => response.json())
    .then(data => {
        let completed_challenges = data
            .filter(item => item.completed)  // Filter out items where completed is false
            .map(item => item.title);       // Map to get only the titles of the remaining items
        hide_challenges(completed_challenges);              // Do something with the titles (e.g., print them to the console)
    })
    .catch(error => console.error('Error:', error));
