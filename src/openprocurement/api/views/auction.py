# -*- coding: utf-8 -*-
from logging import getLogger
from openprocurement.api.utils import (
    save_tender,
    apply_patch,
    add_next_award,
    opresource,
    json_view,
    context_unpack,
)
from openprocurement.api.validation import (
    validate_tender_auction_data,
)


LOGGER = getLogger(__name__)


@opresource(name='Tender Auction',
            collection_path='/tenders/{tender_id}/auction',
            path='/tenders/{tender_id}/auction/{auction_lot_id}',
            description="Tender auction data")
class TenderAuctionResource(object):

    def __init__(self, request):
        self.request = request
        self.db = request.registry.db

    @json_view(permission='auction')
    def collection_get(self):
        """Get auction info.

        Get tender auction info
        -----------------------

        Example request to get tender auction information:

        .. sourcecode:: http

            GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
            Host: example.com
            Accept: application/json

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": {
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "bids": [
                        {
                            "value": {
                                "amount": 500,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": true
                            }
                        },
                        {
                            "value": {
                                "amount": 485,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": true
                            }
                        }
                    ],
                    "minimalStep":{
                        "amount": 35,
                        "currency": "UAH"
                    },
                    "tenderPeriod":{
                        "startDate": "2014-11-04T08:00:00"
                    }
                }
            }

        """
        if self.request.validated['tender_status'] != 'active.auction':
            self.request.errors.add('body', 'data', 'Can\'t get auction info in current ({}) tender status'.format(self.request.validated['tender_status']))
            self.request.errors.status = 403
            return
        return {'data': self.request.validated['tender'].serialize("auction_view")}

    @json_view(content_type="application/json", permission='auction', validators=(validate_tender_auction_data))
    def collection_patch(self):
        """Set urls for access to auction.
        """
        if apply_patch(self.request, src=self.request.validated['tender_src']):
            LOGGER.info('Updated auction urls', extra={'MESSAGE_ID': 'tender_auction_patch'})
            return {'data': self.request.validated['tender'].serialize("auction_view")}

    @json_view(content_type="application/json", permission='auction', validators=(validate_tender_auction_data))
    def collection_post(self):
        """Report auction results.

        Report auction results
        ----------------------

        Example request to report auction results:

        .. sourcecode:: http

            POST /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
            Host: example.com
            Accept: application/json

            {
                "data": {
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "bids": [
                        {
                            "value": {
                                "amount": 400,
                                "currency": "UAH"
                            }
                        },
                        {
                            "value": {
                                "amount": 385,
                                "currency": "UAH"
                            }
                        }
                    ]
                }
            }

        This is what one should expect in response:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Content-Type: application/json

            {
                "data": {
                    "dateModified": "2014-10-27T08:06:58.158Z",
                    "bids": [
                        {
                            "value": {
                                "amount": 400,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": true
                            }
                        },
                        {
                            "value": {
                                "amount": 385,
                                "currency": "UAH",
                                "valueAddedTaxIncluded": true
                            }
                        }
                    ],
                    "minimalStep":{
                        "amount": 35,
                        "currency": "UAH"
                    },
                    "tenderPeriod":{
                        "startDate": "2014-11-04T08:00:00"
                    }
                }
            }

        """
        apply_patch(self.request, save=False, src=self.request.validated['tender_src'])
        if all([i.auctionPeriod and i.auctionPeriod.endDate for i in self.request.validated['tender'].lots if i.numberOfBids > 1]):
            add_next_award(self.request)
        if save_tender(self.request):
            LOGGER.info('Report auction results', extra={'MESSAGE_ID': 'tender_auction_post'})
            return {'data': self.request.validated['tender'].serialize(self.request.validated['tender'].status)}

    @json_view(content_type="application/json", permission='auction', validators=(validate_tender_auction_data))
    def patch(self):
        """Set urls for access to auction for lot.
        """
        if apply_patch(self.request, src=self.request.validated['tender_src']):
            LOGGER.info('Updated auction urls', extra={'MESSAGE_ID': 'tender_lot_auction_patch'})
            return {'data': self.request.validated['tender'].serialize("auction_view")}

    @json_view(content_type="application/json", permission='auction', validators=(validate_tender_auction_data))
    def post(self):
        """Report auction results for lot.
        """
        apply_patch(self.request, save=False, src=self.request.validated['tender_src'])
        if all([i.auctionPeriod and i.auctionPeriod.endDate for i in self.request.validated['tender'].lots if i.numberOfBids > 1]):
            add_next_award(self.request)
        if save_tender(self.request):
            LOGGER.info('Report auction results', extra={'MESSAGE_ID': 'tender_lot_auction_post'})
            return {'data': self.request.validated['tender'].serialize(self.request.validated['tender'].status)}
