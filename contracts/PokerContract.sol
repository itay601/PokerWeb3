// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.27;

contract Poker {
    struct Player {
        address payable playerAddress;
        bool isParticipating;
        uint256 chips;
    }

    struct Game {
        uint256 gameId;
        address dealer;
        uint256 pot;
        uint256 buyIn;
        Player[] players;
        bool isActive;
    }

    mapping(uint256 => Game) public games;
    uint256 public gameCount;

    event GameCreated(uint256 indexed gameId, address indexed dealer, uint256 buyIn);
    event PlayerJoined(uint256 indexed gameId, address indexed player);
    event GameStarted(uint256 indexed gameId);
    event GameEnded(uint256 indexed gameId, address winner);

    modifier onlyDealer(uint256 _gameId) {
        require(msg.sender == games[_gameId].dealer, "Not the dealer");
        _;
    }

    modifier gameActive(uint256 _gameId) {
        require(games[_gameId].isActive, "Game is not active");
        _;
    }

    function createGame(uint256 _buyIn) external {
        gameCount++;
        Game storage newGame = games[gameCount];
        newGame.gameId = gameCount;
        newGame.dealer = msg.sender;
        newGame.buyIn = _buyIn;
        newGame.isActive = true;

        emit GameCreated(gameCount, msg.sender, _buyIn);
    }

    function joinGame(uint256 _gameId) external payable gameActive(_gameId) {
        Game storage game = games[_gameId];
        require(msg.value == game.buyIn, "Incorrect buy-in amount");
        
        game.players.push(Player({
            playerAddress: payable(msg.sender),
            isParticipating: true,
            chips: msg.value
        }));
        
        game.pot += msg.value;

        emit PlayerJoined(_gameId, msg.sender);
    }

    function startGame(uint256 _gameId) external onlyDealer(_gameId) gameActive(_gameId) {
        // Placeholder for starting game logic
        emit GameStarted(_gameId);
    }

    function endGame(uint256 _gameId, address payable _winner) external onlyDealer(_gameId) gameActive(_gameId) {
        Game storage game = games[_gameId];
        game.isActive = false;

        _winner.transfer(game.pot);
        emit GameEnded(_gameId, _winner);
    }
}