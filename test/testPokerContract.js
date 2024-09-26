// test/Poker.test.js

const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Poker Contract", function () {
    let Poker;
    let poker;
    let owner, player1, player2;

    beforeEach(async function () {
        Poker = await ethers.getContractFactory("Poker");
        [owner, player1, player2] = await ethers.getSigners();
        poker = await Poker.deploy();
//        await poker.deployed();
    });

    describe("Game Creation", function () {
        it("should create a game", async function () {
            await poker.createGame(ethers.utils.parseEther("1"));
            const game = await poker.games(1);
            expect(game.dealer).to.equal(owner.address);
            expect(game.buyIn).to.equal(ethers.utils.parseEther("1"));
            expect(game.isActive).to.be.true;
        });

        it("should emit GameCreated event", async function () {
            await expect(poker.createGame(ethers.utils.parseEther("1")))
                .to.emit(poker, "GameCreated")
                .withArgs(1, owner.address, ethers.utils.parseEther("1"));
        });
    });

    describe("Joining a Game", function () {
        beforeEach(async function () {
            await poker.createGame(ethers.utils.parseEther("1"));
        });

        it("should allow a player to join the game", async function () {
            await poker.connect(player1).joinGame(1, { value: ethers.utils.parseEther("1") });
            const game = await poker.games(1);
            expect(game.players.length).to.equal(1);
            expect(game.players[0].playerAddress).to.equal(player1.address);
        });

        it("should emit PlayerJoined event", async function () {
            await expect(poker.connect(player1).joinGame(1, { value: ethers.utils.parseEther("1") }))
                .to.emit(poker, "PlayerJoined")
                .withArgs(1, player1.address);
        });

        it("should revert if buy-in amount is incorrect", async function () {
            await expect(poker.connect(player1).joinGame(1, { value: ethers.utils.parseEther("0.5") }))
                .to.be.revertedWith("Incorrect buy-in amount");
        });
    });

    describe("Starting a Game", function () {
        beforeEach(async function () {
            await poker.createGame(ethers.utils.parseEther("1"));
            await poker.connect(player1).joinGame(1, { value: ethers.utils.parseEther("1") });
        });

        it("should allow the dealer to start the game", async function () {
            await poker.startGame(1);
            const game = await poker.games(1);
            expect(game.currentState).to.equal(0); // PreFlop
        });

        it("should emit GameStarted event", async function () {
            await expect(poker.startGame(1))
                .to.emit(poker, "GameStarted")
                .withArgs(1);
        });

        it("should revert if a non-dealer tries to start the game", async function () {
            await expect(poker.connect(player2).startGame(1))
                .to.be.revertedWith("Not the dealer");
        });
    });

    describe("Game Actions", function () {
        beforeEach(async function () {
            await poker.createGame(ethers.utils.parseEther("1"));
            await poker.connect(player1).joinGame(1, { value: ethers.utils.parseEther("1") });
            await poker.startGame(1);
        });

        it("should allow a player to make a bet", async function () {
            await poker.connect(player1).bet(1, ethers.utils.parseEther("2"));
            const game = await poker.games(1);
            expect(game.currentBet).to.equal(ethers.utils.parseEther("2"));
        });

        it("should emit PlayerAction event on bet", async function () {
            await expect(poker.connect(player1).bet(1, ethers.utils.parseEther("2")))
                .to.emit(poker, "PlayerAction")
                .withArgs(1, player1.address, "Bet", ethers.utils.parseEther("2"));
        });

        it("should revert if the bet is not higher than the current bet", async function () {
            await poker.connect(player1).bet(1, ethers.utils.parseEther("2"));
            await expect(poker.connect(player1).bet(1, ethers.utils.parseEther("1")))
                .to.be.revertedWith("Bet must be higher than current bet");
        });

        // Additional tests for call, raise, fold, endGame...

    });

    describe("Ending a Game", function () {
        beforeEach(async function () {
            await poker.createGame(ethers.utils.parseEther("1"));
            await poker.connect(player1).joinGame(1, { value: ethers.utils.parseEther("1") });
            await poker.startGame(1);
        });

        it("should allow the dealer to end the game", async function () {
            await poker.endGame(1, player1.address);
            const game = await poker.games(1);
            expect(game.isActive).to.be.false;
        });

        it("should emit GameEnded event", async function () {
            await expect(poker.endGame(1, player1.address))
                .to.emit(poker, "GameEnded")
                .withArgs(1, player1.address);
        });

        it("should revert if a non-dealer tries to end the game", async function () {
            await expect(poker.connect(player2).endGame(1, player1.address))
                .to.be.revertedWith("Not the dealer");
        });
    });

    // Additional tests for edge cases and error handling...
});
