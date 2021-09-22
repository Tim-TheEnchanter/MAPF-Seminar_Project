% define global deadline
globaldeadline(DL) :- deadline(DL).

% definition of all directions
dir(1,0). dir(-1,0). dir(0,1). dir(0,-1). dir(0,0).

% only one destination per instance
goal(R,X,Y) :- init(object(destination,R), value(at,(X,Y))).
robot(R)    :- init(object(robot,R), _).

% defining the fixed routes of previously gained paths. Z for robots that behave like zombies.
fixedroute(Z,X,Y,0) :- init(object(robot,Z), value(at,(X,Y))), goal(R,_,_), Z!=R.
fixedroute(Z,X+Dx,Y+Dy,T+1) :- fixedroute(Z,X,Y,T), occurs(object(robot, Z), action(move,(Dx, Dy)),T).

% define nodes
nd(N,X,Y) :- init(object(node,N),value(_,(X,Y))).
% define edges between two adjacent nodes
edge(X,Y, X+Dx,Y+Dy) :- nd(N,X,Y), nd(NN,X+Dx,Y+Dy), dir(Dx,Dy).
edge(X,Y,XX,YY) :- edge(XX,YY,X,Y).

% this should only be one robot!
path(R,X,Y,0) :- init(object(robot,R), value(at,(X,Y))), goal(R,_,_).

{path(R,XX,YY,T+1)}1 :- path(R,X,Y,T), edge(X,Y,XX,YY), globaldeadline(DL), T < DL.

% robot cannot move in different directions at the same timestep
:- path(R,X,Y,T), path(R,XX,YY,T), (X,Y)!= (XX,YY).
%robot doesnt move after goal is reached
:- path(R,X,Y,T), goal(R,X,Y), path(R,_,_,T+1).
% robot may not interfere with already planned routes.
:- path(R,X,Y,T) ,fixedroute(_,X,Y,T). %, (X,Y) == (XX,YY).
% a robot and a zombie cannot switch places
:- path(R,X,Y,T), path(R,XX,YY,T+1), fixedroute(Z,XX,YY,T), fixedroute(Z,X,Y,T+1).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% TODO: write constraint that forbids driving over zombies when they have stopped moving. This may be not necessary when prioritizing by plan length.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

finish(R,T,X,Y) :- path(R,X,Y,T), goal(R,X,Y).

:- not finish(_,_,_,_).

occurs(object(robot, R), action(move,(XX-X, YY-Y)),T) :- path(R,X,Y,T),path(R,XX,YY,T+1).
#show occurs/3.

%#maximize{ R : finish(R,T,_,_)}.
%#minimize{ T : finish(R,T,_,_)}.

#minimize{ T@1,R : finish(R,T,_,_) ; 0@1,0}.
