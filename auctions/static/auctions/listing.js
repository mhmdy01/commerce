// if bidding failed, display any errors to user
function renderBidFormErrors(bidForm, errorsObj) {
    for (let [field, errors] of Object.entries(errorsObj)) {
        const priceField = bidForm.querySelector(`[name="${field}"]`)

        // MUST remove previous errors -if any- first
        priceField.parentElement.querySelectorAll('.alert').forEach(elm => elm.remove());

        // render new errors
        errors.forEach(err => {
            const errrDiv = `<div class="alert alert-danger">${err.message}</div>`
            priceField.parentElement.insertAdjacentHTML('afterbegin', errrDiv);
        })
    }
}

// after successful bids
// reset price field and remove any errors in bidding form
// then show new bids count
function updateBidsCount(bidForm) {
    const priceField = bidForm.querySelector(`[name="price"]`);
    priceField.value = '';
    priceField.parentElement.querySelectorAll('.alert').forEach(elm => elm.remove());

    const oldBidsCount = parseInt(bidForm.previousElementSibling.textContent.match(/\d+/));
    const newBidsCount = oldBidsCount + 1;
    bidForm.previousElementSibling.textContent = `${newBidsCount} bids so far. Your Bid is the Current Bid`;
}

// send an http request
async function sendRequest(url, method='GET', headers={}, body=null) {
    const reqHeaders = new Headers(headers)
    const reqConfig = {
        method: method,
        headers: reqHeaders,
        body: body
    }
    if (reqConfig.method == 'POST' || reqConfig.method == 'PUT') {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        reqConfig.headers.append('X-CSRFToken', csrftoken);
    }
    const req = new Request(url, reqConfig);

    // send req and handle network errors
    // eg. couldn't send request (no internet)
    let res;
    try {
        res = await fetch(req);
    } catch (error) {
        console.log(error);
    }

    // get response body and handle server errors
    // eg. unauthorized action
    // this is done manually and separately from fetch error handling
    // as fetch ONLY REJECT @network errors NOT http status codes
    // eg. responses with status code != 200
    // check: https://www.tjvantoll.com/2015/09/13/fetch-and-errors/
    // response body could be json or not json
    // not json will mainly be plaintext or html
    // nothing more to expect
    // because we control response content-type at server!
    if (res.headers.get('content-type').match(/json/i)) {
        var resBody = await res.json();
    } else {
        var resBody = await res.text();
    }
    if (res.ok) {
        return resBody;
    } else {
        throw new Error(resBody);
    }
}

// when user bid on listing
// send a post request to server to create a new bid
async function placeBid(listingId, bidForm) {
    const body = new URLSearchParams({
        price: bidForm.querySelector('[name="price"]').value,
    });
    const headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    };

    try {
        const resBody = await sendRequest(`/listings/${listingId}/bid`, 'POST', headers, body);
        // display new bids count
        updateBidsCount(bidForm);
    } catch (error) {
        console.log(`place_bid | error | ${error.message}`);
        // display any errors to user
        // but must parse error msg back to js object
        const errorObj = JSON.parse(error.message);
        renderBidFormErrors(bidForm, errorObj);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const listingDiv = document.querySelector('div.listing-details');
    const listingId = listingDiv.dataset.id;
    const bidForm = listingDiv.querySelector('.bid-form')

    bidForm.onsubmit = () => {
        placeBid(listingId, bidForm);

        // disable default form submission behavior
        return false;
    }
})
