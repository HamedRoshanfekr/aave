from scripts.helper import get_account, FORKED_LOCAL_ENVIRONMENT
from brownie import config, network, interface
from scripts.get_weth import get_weth
from web3 import Web3

_amount = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in FORKED_LOCAL_ENVIRONMENT:
        get_weth()
    lending_pool = get_lending_pool()
    approve_erc20(_amount, lending_pool.address, erc20_address, account)
    print("depositing...")
    tx = lending_pool.deposit(erc20_address, _amount, account, 0, {"from": account})
    tx.wait(1)
    print("deposited")
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    dai_eth_price = get_asset_price(config["networks"][network.show_active()]["dai_eth_price_feed"])
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"we are going to borrow {amount_dai_to_borrow} dai")
    borrow_tx = lending_pool.borrow(config["networks"][network.show_active()]["dai_token"],
                        Web3.toWei(amount_dai_to_borrow, "ether"),
                        1, 0, account, {"from": account}
                        )
    borrow_tx.wait(1)
    print("we borrowed some dai")
    get_borrowable_data(lending_pool, account)
    repay_all(Web3.toWei(amount_dai_to_borrow, "ether"), lending_pool, account)

def repay_all(amount, lending_pool, account):
    approve_erc20(Web3.toWei(amount, "ether"), lending_pool.address, config["networks"][network.show_active()]["dai_token"], account)
    tx = lending_pool.repay(config["networks"][network.show_active()]["dai_token"], amount, 1, account, {"from": account})
    tx.wait(1)
    print("repaid!")

def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.IAggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"dai eth price is {converted_latest_price}")
    return float(converted_latest_price)


def get_borrowable_data(lending_pool, account):
    (totalCollateralETH,
     totalDebtETH,
     availableBorrowsETH,
     currentLiquidationThreshold,
     ltv,
     healthFactor) = lending_pool.getUserAccountData(account)
    totalCollateralETH = Web3.fromWei(totalCollateralETH, "ether")
    totalDebtETH = Web3.fromWei(totalDebtETH, "ether")
    availableBorrowsETH = Web3.fromWei(availableBorrowsETH, "ether")
    print(f"you have {totalCollateralETH} worth of eth deposited")
    print(f"you have {totalDebtETH} worth of eth borrowed")
    print(f"you can borrow {availableBorrowsETH} worth of eth")
    return (float(availableBorrowsETH), float(totalDebtETH))


def approve_erc20(amount, spender, erc20_address, account):
    print("approving erc20 token")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("approved")
    return tx


def get_lending_pool():
    lending_poll_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"])
    lending_pool_address = lending_poll_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool
