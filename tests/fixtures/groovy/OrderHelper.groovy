package org.apache.ofbiz.order;

import org.apache.ofbiz.party.PartyServices;

class OrderHelper {
    static Map approveOrder(String orderId) {
        def party = PartyServices.getParty(orderId);
        logApproval(orderId);
        return party;
    }

    static void logApproval(String orderId) {
        System.out.println(orderId);
    }
}
