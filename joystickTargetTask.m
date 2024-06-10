%%ジョイスティックを用いた運動主体感の課題
%% 事前設定

tic

DEBUG = false;
rng('shuffle')

clear SubName;
SubName = input('Input the name of the participant:', 's');
if isempty(SubName) 
    return;
end

clear isPracticeMsg;
isPracticeMsg = input('is this a practice? (y/n):', 's');
if isempty(isPracticeMsg)
    return;
elseif strcmp(isPracticeMsg, 'y')
    isPractice = true;
elseif strcmp(isPracticeMsg, 'n')
    isPractice = false;
else
    return;
end

% needFundamentalPractice = input('do you need fundamental practice? (y):', 's');
% if strcmp(needFundamentalPractice, 'y')
%     fundamentalPractice = true;
% else
%     fundamentalPractice = false;
% end

% isDebugMsg = input('do you need debug messages? (y):', 's');
% if strcmp(isDebugMsg, 'y')
%     DEBUG = true;
% end
DEBUG = false;

tmpdatestr = datestr(now, 30);

% home path
home_path = pwd;

%試行数に関する設定
repeats = 6; %各ブロックにおける各条件の繰り返し回数
practiceRepeats = 1;
practiceTrials = 10; %練習のtrial数
breakTrials = 40; %試行ごとに休憩を取る
fontsize = 30; %フォントサイズ
intervalPractice = 1;
intervalActual = 3;
messageWaitSec = 3;

conditions{1} = [0, 10, 20, 30, 40]; %angular bias
conditions{2} = [0, 5, 10, 15, 20]; %expectation error
conditionSum = length(conditions{1}) * length(conditions{2});
%試行を定義
trial = struct('AngularBias', 0, 'ExpectationError', 0, 'Agency', 0, 'Efficacy', 0, ...
    'SuccessFlag', false, 'AxesArr', zeros(2000, 0), 'TargetArr', [], 'TargetFunc', [], 'TargetStart', 0, 'OriginalError', 0);
% AngularBias ボールの飛ぶ角度とジョイスティック入力との差分．degree
% ExpectationError ボールの最終位置と目標との差分．degree
% Agency 「ボールがどのくらい制御できたと思いますか」の回答
% Efficacy 「今回はどのくらい当てられると思いますか」の回答
% SuccessFlag ボールが目標に当たったかどうか true/false
% AxesArr ジョイスティック入力．ジョイスティックが(0, 0)から外れて，x, yどちらかが1に達するまで．右と上を正とする座標系
% TargetArr 目標の移動軌跡（degree）．ボール初期位置を原点とし，右を0°とする極座標系．45°～135°
% TargetFunc 目標の速度関数f(x). fはradian, xは時間(s)．積分してTargetStartを足すと位置がわかる
% TargetStart 目標の初期位置（degree）．目標の左端をゼロとし，往復の間のランダム値をとる．0°～90°の場合その位置から右へ，90°~180°の場合その位置から左へ目標は進む．
% OriginalError 目標が最後までTargetFuncにしたがって（expectation errorに依る操作なく）移動した場合に，最終的にボールと目標がどのくらいずれていたか．目標の方がボールより左にあった場合に正（degree）．
if isPractice
    trialRepeats = practiceRepeats;
else
    trialRepeats = repeats;
end
trialSum = trialRepeats * conditionSum;
recordTitleStr = 'participant, trial no., angular bias, expectation error, controllability, successibility';
trialList = repmat(trial, 1, trialSum);

tmpCounter = 0;
for repeat = 1 : trialRepeats
    for condition1 = 1 : length(conditions{1})
        for condition2 = 1 : length(conditions{2})
            tmpCounter = tmpCounter + 1;
            trialList(tmpCounter).AngularBias = conditions{1}(condition1);
            trialList(tmpCounter).ExpectationError = conditions{2}(condition2);
            if rand < 0.5 %半分の確率でマイナスにする
                trialList(tmpCounter).AngularBias = -1 * trialList(tmpCounter).AngularBias;
            end
            if rand < 0.5
                trialList(tmpCounter).ExpectationError = -1 * trialList(tmpCounter).ExpectationError;
            end
        end
    end
end

%randomize
randomInd = randperm(trialSum);
trialList = trialList(randomInd);

% if isPractice
%     for counter = 1 : fix(practiceTrials / 2)
%         trialList(counter).ExpectationError = 0;
%     end
% end

joycon = joystickControl();

try
    
    %% 練習: 静止目標に10回連続で当てればクリア
    
%     if fundamentalPractice
%         msg = 'ジョイスティックを倒して点を移動させ，バーに当ててください\n準備ができたら教えてください．';
%         joycon.showMessage('Center', double(msg), true);
%         joycon.waitSpace();
%         counter = 0;
%         successCounter = 0;
%         while successCounter < 5
%             syms f(x);
%             f = pi * rand * dirac(x);
%             [successFlag, axesArr] = joycon.taskExecute(f, 'Symbolic', 0, 0, 0, true, false);
%             counter = counter + 1;
%             if successFlag
%                 successCounter = successCounter + 1;
%                 if DEBUG
%                     joycon.showMessage('LeftTop', 'success', true);
%                     WaitSecs(1);
%                 end
%             else
%                 successCounter = 0;
%                 if DEBUG
%                     joycon.showMessage('LeftTop', 'failure', true);
%                     WaitSecs(1);
%                 end
%             end
%         end
%     end
    
    %% 本番（isPracticeがtrueの場合は練習）
    
    msg = 'ジョイスティックを倒して点を移動させ，動くバーに当ててください\n準備ができたら教えてください．';
    joycon.showMessage('Center', double(msg), true);
    joycon.waitSpace();
    if isPractice
        trialSum = practiceTrials;
    end
    for counter = 1 : trialSum
        if mod(counter, breakTrials) == 1 && counter ~= 1
            msg = '少し休憩を取ってください．再開の準備ができたら教えてください．';
            joycon.showMessage('Center', double(msg), true);
            joycon.waitSpace();
        end
%         if isPractice && mod(counter, round(trialSum / 2)) == 1 && counter ~= 1
%             msg = 'ジョイスティックを倒して点を移動させ，動くバーに当ててください\n準備ができたら教えてください．';
%             joycon.showMessage('Center', double(msg), true);
%             joycon.waitSpace();
%         end
        joycon.showMessage('Center', double([num2str(counter), '回目']), true);
        %joycon.waitClick();
        WaitSecs(1);
%         if DEBUG
%             joycon.showMessage('LeftTop', sprintf('Angular bias: %d, Expectation error: %d', trialList(counter).AngularBias, trialList(counter).ExpectationError), true);
%             WaitSecs(1);
%         end
%         if ~(isPractice && (counter <= trialSum / 2))
%             msg1 = '今回はどのくらい当てられると思いますか';
%             msg2 = '必ず当てられる';
%             msg3 = '全く当てられない';
%             trialList(counter).Efficacy = joycon.measureAgency(double(msg1), double(msg2), double(msg3));
%         end
        noErrorFlag = false;
        hideTargetFlag = false;
        a = rand;
        b = rand;
        c = rand;
        d = rand;
        f = @(x)(a + b * sin(c * x + d));
%         if isPractice && (counter <= trialSum / 2)
%             %f = @(x)(0 * x);
%             noErrorFlag = true;
%             hideTargetFlag = true;
%         end
        trialList(counter).TargetFunc = f;
        tmp_targetStart = pi * rand;
        trialList(counter).TargetStart = rad2deg(tmp_targetStart);
        clear tmp_successFlag tmp_axesArr tmp_targetArr tmp_originalError
        [tmp_successFlag, tmp_axesArr, tmp_targetArr, tmp_originalError] = joycon.taskExecute(f, 'FuncHandler', ...
            deg2rad(trialList(counter).AngularBias), deg2rad(trialList(counter).ExpectationError), tmp_targetStart, noErrorFlag, hideTargetFlag);
        trialList(counter).SuccessFlag = tmp_successFlag;
        trialList(counter).AxesArr = tmp_axesArr;
        trialList(counter).TargetArr = rad2deg(tmp_targetArr);
        trialList(counter).OriginalError = rad2deg(tmp_originalError);
        msg1 = 'ボールの軌道に対してどのくらい制御できたと思いますか';
        msg2 = '良く制御できた';
        msg3 = '全く制御できていなかった';
        trialList(counter).Agency = joycon.measureAgency(double(msg1), double(msg2), double(msg3));
%         if DEBUG
%             if trialList(counter).SuccessFlag
%                 joycon.showMessage('LeftTop', 'success', true);
%             else
%                 joycon.showMessage('LeftTop', 'failure', true);
%             end
%             WaitSecs(1);
%         end
    end
    
    %% 保存と終了
    
    if isPractice
        msg = '以上で練習は終了です';
        joycon.showMessage('Center', double(msg), true);
    else
        msg = '以上で終了です．ありがとうございました．';
        joycon.showMessage('Center', double(msg), true);
    end
    joycon.waitSpace();
    trialListTable = struct2table(trialList);
    if isPractice
        filename = sprintf('%s_%s_practice', SubName, tmpdatestr);
    else
        filename = sprintf('%s_%s_result', SubName, tmpdatestr);
    end
    save(filename, 'trialListTable');
    
    joycon.delete(); 
    toc
    
catch ME
    joycon.delete();
    trialListTable = struct2table(trialList);
    if isPractice
        filename = sprintf('%s_%s_practice', SubName, tmpdatestr);
    else
        filename = sprintf('%s_%s_result', SubName, tmpdatestr);
    end
    save(filename, 'trialListTable');
    rethrow(ME);
end
