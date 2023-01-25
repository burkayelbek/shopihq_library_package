from enum import Enum


class CustomerReasonEnum(Enum):
    # ToDo: Should be support in multi-language
    NoReason = 10
    ChangedMyMind = 20
    WithdrawalFromDistanceSales = 30
    WrongItem = 40
    Delayed = 50
    FoundCheaper = 60
    Other = -1


