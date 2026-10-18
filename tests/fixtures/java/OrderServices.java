package org.apache.ofbiz.order;

import org.apache.ofbiz.party.PartyServices;
import java.util.Map;

public class OrderServices {
    public static Map<String, Object> createOrder(String orderTypeId) {
        Map<String, Object> party = PartyServices.getParty(orderTypeId);
        validateOrder(orderTypeId);
        return party;
    }

    private static void validateOrder(String orderTypeId) {
        System.out.println(orderTypeId);
    }
}
