classdef joystickControl
    %JOYSTICKCONTROL ジョイスティックの入力受付と画面への描画
    
    properties
        movingTime; %movingTime秒の間に目的地に到達する
        stayingTime; %目的地にstayingTime秒留まってから戻る
        stimulusSize; %ドットの直径
        minDistance; %joystickを20%以上動かさないと反応しない
        targetWidth; %左右に移動するターゲットの幅の角度
        targetHeight;
        
        spaceKey; %key code of space
        escapeKey; %key to break
        bgColor;
        grayLineColor;
        stimuliColor;
        
        ifi; %フレーム間の時間
        screenWidth;
        screenHeight;
        
        joy;
        win;
        rect;
        
        centerPos;
    end
    
    methods
        function obj = joystickControl()
            %JOYSTICKCONTROL このクラスのインスタンスを作成
            %戻り値 obj joystickControlオブジェクト
            
            try
                KbName('UnifyKeyNames');
                DisableKeysForKbCheck([240, 243, 242, 244]);
                obj.spaceKey = 32; %key code of space
                obj.escapeKey = 27; %key to break
                obj.bgColor = [125 125 125];
                obj.grayLineColor = [100 100 100];
                obj.stimuliColor = [0 0 0]; %刺激black
                obj.movingTime = 0.5; %movingTime秒の間に目的地に到達する
                obj.stayingTime = 0.5; %目的地にstayingTime秒留まってから戻る
                obj.stimulusSize = 50; %ドットの直径
                obj.minDistance = 0.2; %joystickを20%以上動かさないと反応しない
                obj.targetWidth = deg2rad(10); %左右に移動するターゲットの幅の角度
                obj.targetHeight = 6;
                % open a new window
                AssertOpenGL;
                % removes the blue screen flash and minimize extraneous warnings.
                Screen('Preference', 'SkipSyncTests', 1);
                Screen('Preference', 'VisualDebugLevel', 3);
                Screen('Preference', 'SuppressAllWarnings', 1);
                Screen('Preference', 'TextRenderer', 0);
                %Screen('Preference', 'DefaultTextYPositionIsBaseline', 1);
                screenNumber = max(Screen('Screens'));
                [obj.win, obj.rect] = Screen('OpenWindow', screenNumber, obj.bgColor);
                [obj.centerPos(1), obj.centerPos(2)] = RectCenter(obj.rect);
                % duration of each frame
                obj.ifi = Screen('GetFlipInterval', obj.win);
                Screen('TextFont', obj.win, 'MS Gothic');
                HideCursor;
                obj.screenWidth = obj.centerPos(1) * 2;
                obj.screenHeight = obj.centerPos(2) * 2;
                
                %get joystick
                %require Simulink 3D Animation toolbox
                obj.joy = vrjoystick(1);
            catch ME
                obj.delete();
                rethrow(ME);
            end
        end
        
        function  [successFlag, axesArr, targetArr, originalError, joyAngleOriginal] = taskExecute(obj, movingAngleFunc, funcKind, angularBias, expectationError, startPoint, noError, hideTarget)
            %taskExecute タスクを実行
            %引数 movingAngleFunc 開始からの秒数を入力，ターゲット角度(rad)を出力とする関数
            %引数 funcKind シンボリック式か関数ハンドラかを，'Symbolic', 'FuncHandler'で指定
            %引数 angularBias ジョイスティックの角度と刺激の移動の角度の変位（radian）
            %引数 expectationError 刺激が移動開始した瞬間にターゲットがexpectationError分移動する（radian）
            %引数 startPoint targetの開始角度を設定する（radian）
            %引数 noError trueだとexpectation errorを無視する
            %引数 hideTarget ボールが飛ぶとTargetを隠す
            %戻り値 successFlag タスクが成功したか否か
            %戻り値 axesArr ジョイスティックの軌跡（ボールの初期位置を原点とし，右をx, 上をyとする座標系）
            %戻り値 targetArr 目標の軌跡（radian, ボールの初期位置を中心とし，右を0°，左回りを正とする極座標系）
            %戻り値 originalError 目標がそれまで通りに動いた場合，目標とボールがどれだけずれていたか（radian）
            
            try
                escapeFlag = false;
                %x,yはドットの中心の座標
                initialPosition = [obj.centerPos(1), obj.centerPos(2)*1.5];
                destinationY = obj.centerPos(2)/2; %到達点は画面のy座標
                currentPosition = initialPosition;
                endPosition = initialPosition;
                circleRadius = initialPosition(2) - destinationY;
                circleRect = [initialPosition(1) - circleRadius, initialPosition(2) - circleRadius, ...
                    initialPosition(1) + circleRadius, initialPosition(2) + circleRadius];
                tmp_axesArr = zeros(round(60 * 60 * 1 / obj.ifi), 2);
                all_axesArr = tmp_axesArr;
                tmp_targetArr = zeros(round(60 * 60 * 1 / obj.ifi), 1);
                axesPointer = 0;
                
                moveState = 0; %joystickが移動されたかどうか
                frameCounter = 0;
                while ~escapeFlag %escapeが押されるか，1タスク終わるまで画面を描画する。ディスプレイのリフレッシュ率が60Hzの場合1ループは1/60 sかかる
                    if moveState >= 0 %movingStateがマイナスの場合はドットが目的地にと止まっている場合なので、この間にターゲットを移動しない
                        frameCounter = frameCounter + 1;
                    end
                    %各フレームにおいてescapeキーが押されているかどうかを判断する。
                    [ keyIsDown, ~, keyCode ] = KbCheck;
                    if keyIsDown && keyCode(obj.escapeKey)
                        escapeFlag = true;
                    end
                    
                    [axes, ~, ~] = read(obj.joy); %各フレームでジョイスティックの状態を読む
                    %axesは4列の数列、1,2列目は座標。座標空間はx, y軸でそれぞれ[-1 ～ +1]であり、正方向空間です。
                    axes(2) = -1 * axes(2); %普通の座標系に変換
                    all_axesArr(frameCounter, :) = axes(1 : 2);
                    %obj.showMessage('LeftTop', sprintf('%d %d', axes(1), axes(2)), false);
                    %画面に投射する際にはjoystickの角度を計算する
                    if moveState == 0 && axes(2) > 0 %上方向へ移動が始まった場合、移動している状態に変え、移動の位置を記録する
                        moveState = 9999;
                        axesPointer = 1;
                        tmp_axesArr(1, :) = axes(1:2); %axesArrは移動の間にjoystickのカーソルの位置を記録する。中身を更新していく。
                    elseif moveState ~= 0 %すでに移動が始まっている場合
                        if (moveState == 9999) && (max(abs(axes(1 : 2))) == 1) %ジョイスティックが限界まで倒されるとドットを移動する．
                            %if (moveState == 9999) && (max(abs(axes(1 : 2))) == 0)
                            %ドットはリアルタイムに動かない、joystickが戻ったら動く
                            hypotArr = hypot(tmp_axesArr(1:axesPointer,1), tmp_axesArr(1:axesPointer,2)); %各フレームの移動距離を計算する
                            [~, ind] = max(hypotArr); %移動距離の最も大きい位置を最終到達位置とし、その角度を計算する
                            if abs(tmp_axesArr(ind, 1)) >= obj.minDistance || abs(tmp_axesArr(ind, 2)) >= obj.minDistance
                                joyAngleOriginal = atan2(tmp_axesArr(ind, 2), tmp_axesArr(ind, 1));
                                %tmpY =  initialPosition(2) - destinationY;
                                %tmpX = abs(tmpY/tan(joyAngle));
                                joyAngle = joyAngleOriginal + angularBias;
                                endPosition(1) = initialPosition(1) + circleRadius * cos(joyAngle);
                                endPosition(2) = initialPosition(2) - circleRadius * sin(joyAngle);
                                if endPosition(1) > obj.screenWidth-obj.stimulusSize %右の枠を超えてしまう場合、yを再計算する
                                    tmpX = obj.screenWidth - obj.stimulusSize - initialPosition(1);
                                    tmpY = tmpX * tan(joyAngle);
                                    endPosition = [obj.screenWidth - obj.stimulusSize, initialPosition(2)-tmpY];
                                elseif endPosition(1) < obj.stimulusSize %左の枠を超えてしまう場合
                                    tmpX = initialPosition(1) - obj.stimulusSize;
                                    tmpY = tmpX * tan(joyAngle);
                                    endPosition = [obj.stimulusSize, initialPosition(2)-tmpY];
                                end
                                moveState = round(1/obj.ifi) * obj.movingTime;
                                %
                            else
                                moveState = 0;
                            end
                            %do something
                        elseif moveState == 9999
                            axesPointer = axesPointer + 1;
                            tmp_axesArr(axesPointer, :) = axes(1:2); %原点に戻っていない場合は移動位置を数列に保持する
                        elseif moveState >= 1 %endPositionに応じて計算する
                            totalFrame = round(1/obj.ifi) * obj.movingTime;
                            shift = endPosition - initialPosition;
                            currentShift = shift ./totalFrame .* (totalFrame - moveState + 1);
                            currentPosition = initialPosition + currentShift;
                            moveState = moveState - 1;
                            if moveState == 0
                                moveState = -1 * round(1/obj.ifi) * obj.stayingTime;
                            end
                        elseif moveState < 0 %原点に戻す
                            moveState = moveState + 1;
                            if moveState == 0
                                currentPosition = initialPosition;
                                %axesArr = zeros(2000, 2);
                                %axesPointer = 0;
                                escapeFlag = true;
                                moveState = -1;
                            end
                        end
                    else
                        currentPosition = initialPosition;
                    end
                    
                    %ラインを描画する
                    Screen('DrawLine', obj.win, obj.grayLineColor, 0, initialPosition(2), obj.screenWidth, initialPosition(2), 2);
                    Screen('FrameArc', obj.win, obj.grayLineColor, circleRect, -45, 90, 2);
                    %ターゲットを描画する
                    switch funcKind
                        case 'FuncHandler'
                            totalMovingAngle = startPoint + integral(movingAngleFunc, 0, frameCounter * obj.ifi);
                        case 'Symbolic'
                            totalMovingAngle = startPoint + int(movingAngleFunc, 0, frameCounter * obj.ifi);
                            totalMovingAngle = double(totalMovingAngle);
                        otherwise
                            error('関数の種類の指定が不正です');
                    end
                    tmpTime = floor(totalMovingAngle / (pi/2));
                    tmpMod = mod(totalMovingAngle, pi/2);
                    if mod(tmpTime, 2) == 0 %偶数、左から右
                        targetAngle = tmpMod - pi/4;
                    else %右から左
                        targetAngle = pi/2 - tmpMod - pi/4;
                    end
                    targetAngle = -targetAngle + pi / 2;
                    if moveState < 0
                        originalError = targetAngle - joyAngleOriginal;
                    end
                    if ~noError %expectationErrorに基づくtargetの変更
                        if 0 < moveState && moveState < 9999 %刺激移動中なら
                            totalFrame = round(1/obj.ifi) * obj.movingTime;
                            diffInOneFrame = (joyAngle + expectationError - targetAngle) / totalFrame;
                            targetAngle = targetAngle + diffInOneFrame * (totalFrame - moveState);
                        elseif moveState < 0 %成否判定中なら
                            targetAngle = joyAngle + expectationError;
                        end
                    end
                    tmp_targetArr(frameCounter) = targetAngle;
                    targetAngle = -targetAngle + pi / 2;
                    %Screen('DrawLine', win, stimuliColor, targetAngle-targetWidth/2, destinationY, targetAngle+targetWidth/2, destinationY, targetHeight);
                    if (~hideTarget) || moveState >= 0 || moveState <= 9999
                        Screen('FrameArc', obj.win, obj.stimuliColor, circleRect, ...
                            rad2deg(targetAngle - obj.targetWidth / 2), rad2deg(obj.targetWidth), obj.targetHeight);
                        targetCenter{1} = initialPosition + circleRadius * 0.99 * [cos(-targetAngle + pi / 2), -sin(-targetAngle + pi / 2)];
                        targetCenter{2} = initialPosition + circleRadius * 1.01 * [cos(-targetAngle + pi / 2), -sin(-targetAngle + pi / 2)];
                        Screen('DrawLine', obj.win, obj.stimuliColor, targetCenter{1}(1), targetCenter{1}(2), targetCenter{2}(1), targetCenter{2}(2), obj.targetHeight);
                    end
                    %刺激のドットを描画する
                    stimulusPos = [currentPosition(1)-obj.stimulusSize/2, currentPosition(2)-obj.stimulusSize/2, currentPosition(1)+obj.stimulusSize/2, currentPosition(2)+obj.stimulusSize/2];
                    Screen('FillOval', obj.win, obj.stimuliColor, stimulusPos);
                    Screen('Flip', obj.win);
                    if moveState < 0 % 成否の判定
                        targetAngle = -targetAngle + pi / 2;
                        if abs(targetAngle - joyAngle) <= (obj.targetWidth / 2) %targetの描画域内に中心が入っていたら
                            successFlag = true;
                        else
                            successFlag = false;
                        end
                        %obj.showMessage('LeftTop', sprintf('%d %d', rad2deg(targetAngle), rad2deg(joyAngle)), false);
                    end
                end
                targetArr = tmp_targetArr(1 : frameCounter);
                axesArr = all_axesArr(1 : frameCounter, :);
            catch ME
                obj.delete();
                rethrow(ME);
            end
        end
        
        function showMessage(obj, place, message, flip, varargin)
            %画面上にテキストを出す
            %引数 obj joystickControlオブジェクト
            %引数 place 左上か真ん中か．'LeftTop', or 'Center' or それ以外の文字列（任意）
            %引数 message テキスト．\nを含んでよい．
            %引数 filp 画面をflipする
            %オプション引数 placeでそれ以外の文字列の場合，座標を[x y]で指定
            
            try
                newlinepos = strfind(message, '\n');
                if isempty(newlinepos)
                    messages{1} = message;
                else
                    messages{length(newlinepos) + 1} = [];
                    messages{1} = message(1 : newlinepos(1) - 1);
                    for count = 2 : (length(newlinepos) - 1)
                        messages{count} = message(newlinepos(count - 1) + 2 : newlinepos(count) - 1);
                    end
                    messages{end} = message(newlinepos(end) + 2 : end);
                end
                switch place
                    case 'LeftTop'
                        defaultX = 0;
                        defaultY = 0;
                    case 'Center'
                        defaultX = obj.centerPos(1);
                        defaultY = obj.centerPos(2);
                    otherwise
                        defaultX = varargin{1}(1);
                        defaultY = varargin{1}(2);
                end
                StartX = 0;
                StartY = 0;
                for count = 1 : length(messages)
                    switch place
                        case 'LeftTop'
                            % X=0, Y=0のまま変えない
                            %DrawFormattedText(obj.win, message, 0, 0, [], 0, 0, 0, 3);
                        otherwise
                            [area, ~]= Screen('TextBounds', obj.win, message);%messages{count});
                            StartX = defaultX - (area(RectRight)/2);
                            StartY = defaultY - (area(RectBottom)/2);
                            %DrawFormattedText(obj.win, message, StartX, StartY, [], 0, 0, 0, 3);
                    end
                    Screen('DrawText', obj.win, messages{count}, StartX, StartY);
                    defaultY = defaultY + 100;
                end
                if flip
                    Screen('Flip', obj.win);
                end
            catch ME
                obj.delete();
                rethrow(ME);
            end
        end
        
        function agency = measureAgency(obj, mainMessage, rightMessage, leftMessage)
            %バーでagency等を聞く
            %引数 obj joystickControlオブジェクト
            %引数 message バーと同時に出す，被験者への質問文
            %引数 rightMessage バーの右端に出す言葉．「よくできた」等
            %引数 leftMessage バーの左端に出す言葉．「全くできなかった」等
            %戻り値 agency バーで選ばれた点
            
            try
                SetMouse(obj.centerPos(1), obj.centerPos(2));
                ShowCursor;
                flag = true;
                barWidth = 10;
                barHeight = 80;
                cursorBarColor = [50 50 50];
                cursorWidth = 10;
                while flag
                    [ keyIsDown, ~, keyCode ] = KbCheck;
                    [x, ~, buttons] = GetMouse;
                    if keyIsDown || buttons(1)
                        if keyCode(obj.spaceKey) || buttons(1)
                            flag = false;
                        elseif keyCode(obj.escapeKey)
                            flag = false;
                            %escapeFlag = true;
                        end
                        KbReleaseWait;
                    end
                    obj.showMessage('other', mainMessage, false, [obj.centerPos(1), obj.centerPos(2) - 200]);
                    soaBarLength = obj.centerPos(1);
                    soaApex = [-soaBarLength/2, soaBarLength/2, -soaBarLength/2, -soaBarLength/2, soaBarLength/2, soaBarLength/2;...
                        0, 0, -50, 50, -50, 50];
                    Screen('DrawLines', obj.win, soaApex, barWidth, obj.stimuliColor, obj.centerPos);
                    if x-obj.centerPos(1) < - soaBarLength/2
                        x = - soaBarLength/2 + obj.centerPos(1);
                    elseif x-obj.centerPos(1) > soaBarLength/2
                        x = soaBarLength/2 + obj.centerPos(1);
                    end
                    Screen('DrawLines', obj.win, [x-obj.centerPos(1), x-obj.centerPos(1); -barHeight, barHeight], cursorWidth, cursorBarColor, obj.centerPos);
                    obj.showMessage('other', leftMessage, false, [obj.centerPos(1)-soaBarLength/2, obj.centerPos(2) + 100]);
                    obj.showMessage('other', rightMessage, false, [obj.centerPos(1)+soaBarLength/2, obj.centerPos(2) + 100]);
                    Screen('Flip', obj.win);
                end
                agency = (x - obj.centerPos(1) + soaBarLength/2)/soaBarLength;
                HideCursor;
                flag = true;
                while flag %マウスのクリックが離されるまで待つ
                    [~, ~, buttons] = GetMouse;
                    if buttons(1)
                        flag = true;
                    else
                        flag = false;
                    end
                end
            catch ME
                obj.delete();
                rethrow(ME);
            end
        end
        
        function waitSpace(obj)
            flag = true;
            while flag
                [ keyIsDown, ~, keyCode ] = KbCheck;
                if keyIsDown
                    if keyCode(obj.spaceKey)
                        flag = false;
                    elseif keyCode(obj.escapeKey)
                        flag = false;
                    end
                    KbReleaseWait;
                end
            end
        end
        
        function delete(~)
            sca;
        end
    end
    
    methods(Static)
        function waitClick()
            flag = true;
            while flag %マウスのクリックが押されるまで待つ
                [~, ~, buttons] = GetMouse;
                if buttons(1)
                    flag = false;
                else
                    flag = true;
                end
            end
            
            flag = true;
            while flag %マウスのクリックが離されるまで待つ
                [~, ~, buttons] = GetMouse;
                if buttons(1)
                    flag = true;
                else
                    flag = false;
                end
            end
        end
    end
end
